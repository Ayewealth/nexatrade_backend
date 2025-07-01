from django.core.management.base import BaseCommand
from apps.wallets.models import CryptoType
from apps.wallets.utils import get_coinpaprika_coins_cached, get_coinpaprika_logo


class Command(BaseCommand):
    help = "Populate CryptoType from CoinGecko API"

    def handle(self, *args, **kwargs):
        self.stdout.write("Fetching crypto types from CoinGecko...")
        coins = get_coinpaprika_coins_cached()

        # Mark all existing cryptos inactive first (optional but useful)
        CryptoType.objects.update(is_active=False)

        created_count = 0
        updated_count = 0

        for coin in coins:
            if not coin['is_active'] or coin['type'] != 'coin':
                continue

            symbol = coin['symbol'].upper()
            name = coin['name']
            paprika_id = coin['id']

            # logo = get_coinpaprika_logo(paprika_id)

            obj, created = CryptoType.objects.update_or_create(
                symbol=symbol,
                defaults={
                    # "logo_url": logo,
                    "name": name,
                    "coinpaprika_id": paprika_id,
                    "is_active": True
                }
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"CryptoTypes updated: {updated_count}, created: {created_count}"
            )
        )
