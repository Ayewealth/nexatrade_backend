# wallets/models.py
from django.db import models
from apps.authentication.models import User
import uuid


class CryptoType(models.Model):
    """Model for different cryptocurrency types"""
    logo_url = models.URLField(null=True, blank=True)
    name = models.CharField(max_length=100)  # BTC, ETH, etc.
    symbol = models.CharField(max_length=50)
    coingecko_id = models.CharField(max_length=100, blank=True, null=True)
    coinpaprika_id = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.symbol


class Wallet(models.Model):
    """Base wallet model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=24, decimal_places=8, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class CryptoWallet(Wallet):
    """Cryptocurrency wallet model"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='crypto_wallets')
    crypto_type = models.ForeignKey(CryptoType, on_delete=models.CASCADE)
    wallet_address = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.email} - {self.crypto_type.symbol} Wallet"


class USDWallet(Wallet):
    """Special USD wallet for trading"""
    # This wallet is used for trading operations
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='usd_wallets')

    def __str__(self):
        return f"{self.user.email} - USD Wallet"


class Transaction(models.Model):
    """Model for deposit and withdrawal transactions"""
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('conversion', 'Conversion'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(
        max_length=15, choices=TRANSACTION_TYPES)  # Increased length for 'conversion'
    crypto_wallet = models.ForeignKey(
        CryptoWallet, on_delete=models.CASCADE, null=True, blank=True)
    usd_wallet = models.ForeignKey(
        USDWallet, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=24, decimal_places=8)  # Crypto amount
    usd_amount = models.DecimalField(
        max_digits=24, decimal_places=8, null=True, blank=True)  # USD equivalent
    conversion_rate = models.DecimalField(
        max_digits=24, decimal_places=8, null=True, blank=True)  # Rate at time of conversion
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='pending')
    external_address = models.CharField(
        max_length=100, blank=True, null=True)  # For withdrawals
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)  # Admin notes

    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} - {self.amount}"
