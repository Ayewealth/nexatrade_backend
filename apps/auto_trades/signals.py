# auto_trades/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import PackageSubscription
from apps.wallets.models import USDWallet


@receiver(post_save, sender=PackageSubscription)
def check_package_completion(sender, instance, created, **kwargs):
    """Check if a package subscription has completed"""
    if not created and instance.status == 'active' and timezone.now() >= instance.end_date:
        # Package has completed
        instance.status = 'completed'
        instance.save(update_fields=['status'])

        # Add investment amount plus profit to user's USD wallet
        usd_wallet, created = USDWallet.objects.get_or_create(
            user=instance.user,
            defaults={'balance': 0}
        )

        # Calculate total return (investment + profit)
        total_return = instance.investment_amount + instance.expected_profit

        # Add funds to wallet
        usd_wallet.balance += total_return
        usd_wallet.save()
