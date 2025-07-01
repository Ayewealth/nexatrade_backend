from django.core.management.base import BaseCommand
from apps.wallets.models import CryptoType
from apps.wallets.utils import get_coinpaprika_logo


class Command(BaseCommand):
    help = "Fetch and update logos for all CryptoType entries from CoinPaprika"

    def handle(self, *args, **kwargs):
        cryptos = CryptoType.objects.all()
        updated_count = 0
        skipped = 0

        for crypto in cryptos:
            # You must have stored CoinPaprika ID during creation
            if not hasattr(crypto, 'coinpaprika_id') or not crypto.coinpaprika_id:
                self.stdout.write(self.style.WARNING(
                    f"Skipped {crypto.symbol}: No coinpaprika_id"))
                skipped += 1
                continue

            logo = get_coinpaprika_logo(crypto.coinpaprika_id)

            if logo:
                crypto.logo_url = logo
                crypto.save(update_fields=["logo_url"])
                updated_count += 1
                self.stdout.write(f"Updated logo for {crypto.symbol}")
            else:
                self.stdout.write(self.style.WARNING(
                    f"No logo found for {crypto.symbol}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Logo update complete: {updated_count} updated, {skipped} skipped")
        )
