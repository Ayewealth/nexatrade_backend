from django.core.management.base import BaseCommand
from apps.auto_trades.services import AutoTradingService


class Command(BaseCommand):
    help = 'Manually trigger auto-trading for active subscriptions'

    def handle(self, *args, **options):
        created_trades = AutoTradingService.process_active_subscriptions()
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(created_trades)} auto-trades'
            )
        )
