from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Runs initial population scripts for wallets and trading apps'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Initializing data..."))

        try:
            call_command('populate_cryptotypes')
            self.stdout.write(self.style.SUCCESS(
                "CryptoType model populated with data from CoinGecko."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"Failed to populate crypto types: {e}"))

        try:
            call_command('populate_markets')
            self.stdout.write(self.style.SUCCESS("Markets populated."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"Failed to populate markets: {e}"))

        try:
            call_command('populate_coinpaprika_logo')
            self.stdout.write(self.style.SUCCESS(
                "Updates your CryptoType model with correct CoinPaprika Logo Url."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"Failed to populate crypto types with CoinPaprika Logo Url: {e}"))
