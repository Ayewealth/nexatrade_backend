# authentication/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from apps.wallets.models import CryptoWallet, USDWallet, CryptoType
from apps.wallets.predefined_addresses import PREDEFINED_WALLET_ADDRESSES

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_wallets(sender, instance, created, **kwargs):
    if created:
        # Create USD wallet
        if not USDWallet.objects.filter(user=instance).exists():
            USDWallet.objects.create(user=instance, balance=0)

        # For each active crypto type
        for crypto_type in CryptoType.objects.filter(is_active=True):
            symbol = crypto_type.symbol.upper()

            # Only create wallet if it doesn't exist yet
            if not CryptoWallet.objects.filter(user=instance, crypto_type=crypto_type).exists():
                address_pool = PREDEFINED_WALLET_ADDRESSES.get(symbol)

                if address_pool and len(address_pool) > 0:
                    # Reuse logic: rotate through list by user.id % len
                    index = instance.id % len(address_pool)
                    wallet_address = address_pool[index]

                else:
                    # No available address left — optional: raise an error or skip
                    continue

                # Create crypto wallet with the matched address
                CryptoWallet.objects.create(
                    user=instance,
                    crypto_type=crypto_type,
                    balance=0,
                    wallet_address=wallet_address
                )
