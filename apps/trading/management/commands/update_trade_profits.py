# trading/management/commands/update_trade_profits.py
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.trading.models import Trade, Market
from decimal import Decimal
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Updates profits for all open trades with auto calculation mode'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes to database',
        )

    def handle(self, *args, **options):
        channel_layer = get_channel_layer()
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY RUN mode'))

        # Get all open trades with auto profit calculation
        trades = Trade.objects.filter(
            status='open',
            profit_calculation_mode='auto'
        ).select_related('market')

        updated_count = 0
        error_count = 0

        with transaction.atomic():
            for trade in trades:
                try:
                    # Get current market price
                    market = trade.market
                    current_price = market.current_price

                    if current_price is None or current_price <= 0:
                        self.stdout.write(self.style.WARNING(
                            f'Invalid price for trade {trade.id}: {current_price}'))
                        continue

                    # Calculate profit based on price difference
                    if trade.trade_type == 'buy':
                        profit_percentage = (
                            current_price - trade.price) / trade.price
                    else:  # sell
                        profit_percentage = (
                            trade.price - current_price) / trade.price

                    # Apply leverage
                    profit_percentage *= trade.leverage

                    # Calculate actual profit
                    profit = (trade.amount * trade.price) * profit_percentage

                    if not dry_run:
                        # Update trade
                        trade.current_profit = profit
                        trade.save(update_fields=['current_profit'])

                        async_to_sync(channel_layer.group_send)(
                            "profits",  # name of group for profit updates
                            {
                                "type": "profit_update",
                                "data": {
                                    "trade_id": trade.id,
                                    "user_id": trade.user.id,  # optional: filter by user on frontend
                                    "market": market.name,
                                    "profit": str(profit),
                                    "symbol": market.base_currency.symbol,
                                },
                            }
                        )

                    updated_count += 1

                    if options['verbosity'] >= 2:
                        self.stdout.write(
                            f'Updated trade {trade.id}: profit = {profit:.2f}'
                        )

                except Exception as e:
                    error_count += 1
                    logger.error(f'Error updating trade {trade.id}: {str(e)}')
                    self.stdout.write(self.style.ERROR(
                        f'Error updating trade {trade.id}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(
            f'Successfully {"would update" if dry_run else "updated"} {updated_count} trades'
        ))

        if error_count > 0:
            self.stdout.write(self.style.ERROR(
                f'Encountered {error_count} errors'
            ))
