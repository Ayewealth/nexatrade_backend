from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging
import time

from apps.wallets.models import CryptoType
from apps.trading.models import Market
from apps.trading.utils import get_coinpaprika_tickers_cached

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Updates market prices using CoinPaprika data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making any changes to the database',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        channel_layer = get_channel_layer()

        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY RUN mode'))

        try:
            paprika_data = get_coinpaprika_tickers_cached()
            paprika_index = {
                item['symbol'].upper(): item for item in paprika_data}
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"Failed to fetch CoinPaprika data: {e}"))
            return

        total_created = 0
        total_updated = 0
        total_errors = 0

        active_cryptos = CryptoType.objects.filter(is_active=True)
        total = active_cryptos.count()

        with transaction.atomic():
            for idx, crypto in enumerate(active_cryptos, start=1):
                symbol = crypto.symbol.upper()
                self.stdout.write(f"[{idx}/{total}] Processing {symbol}...")

                if symbol not in paprika_index:
                    self.stdout.write(self.style.WARNING(
                        f"{symbol} not found in CoinPaprika data — skipping."))
                    continue

                item = paprika_index[symbol]
                quotes = item.get('quotes', {})

                existing_market_names = set(Market.objects.filter(
                    base_currency=crypto).values_list('name', flat=True))
                current_market_names = set()

                for quote_symbol, quote_data in quotes.items():
                    try:
                        quote = quote_symbol.upper()
                        market_name = f"{symbol}/{quote}"
                        current_price = Decimal(quote_data['price'])
                        min_trade_amount = Decimal('0.001')

                        current_market_names.add(market_name)

                        if not dry_run:
                            market, created = Market.objects.update_or_create(
                                name=market_name,
                                base_currency=crypto,
                                defaults={
                                    'quote_currency': quote,
                                    'current_price': current_price,
                                    'min_trade_amount': min_trade_amount,
                                    'is_active': True,
                                }
                            )

                            async_to_sync(channel_layer.group_send)(
                                "markets",
                                {
                                    "type": "market_update",
                                    "data": {
                                        "market": market.name,
                                        "price": str(market.current_price),
                                        "symbol": crypto.symbol,
                                    },
                                }
                            )

                        if not dry_run:
                            if created:
                                total_created += 1
                            else:
                                total_updated += 1

                        if options['verbosity'] >= 2:
                            self.stdout.write(
                                f"Updated {market_name}: {current_price}")

                    except Exception as e:
                        total_errors += 1
                        logger.error(
                            f"Error updating {symbol}/{quote_symbol}: {str(e)}")
                        self.stdout.write(self.style.ERROR(
                            f"Error updating {symbol}/{quote_symbol}: {str(e)}"
                        ))

                # Deactivate stale markets
                stale = existing_market_names - current_market_names
                if stale and not dry_run:
                    Market.objects.filter(
                        name__in=stale, base_currency=crypto).update(is_active=False)

                time.sleep(1)

        self.stdout.write(self.style.SUCCESS(
            f'Successfully {"would update" if dry_run else "updated"} markets: '
            f'Created: {total_created}, Updated: {total_updated}'
        ))

        if total_errors > 0:
            self.stdout.write(self.style.ERROR(
                f"Encountered {total_errors} errors"))
