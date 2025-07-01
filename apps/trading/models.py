# trading/models.py
from django.db import models
from apps.authentication.models import User
from apps.wallets.models import CryptoType, USDWallet
import uuid


class Market(models.Model):
    """Trading market model"""
    name = models.CharField(max_length=100)  # BTC/USD, ETH/USD, etc.
    base_currency = models.ForeignKey(
        CryptoType, on_delete=models.CASCADE, related_name='base_markets')
    quote_currency = models.CharField(
        max_length=50, default='USD')  # Usually USD
    is_active = models.BooleanField(default=True)
    current_price = models.DecimalField(max_digits=24, decimal_places=8)
    min_trade_amount = models.DecimalField(
        max_digits=24, decimal_places=8, default=0.001)

    def __str__(self):
        return self.name


class Trade(models.Model):
    """Model for trading operations"""
    TRADE_TYPES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ]

    PROFIT_CALCULATION_MODES = [
        ('auto', 'Automatic'),
        ('manual', 'Manual'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='trades')
    market = models.ForeignKey(Market, on_delete=models.CASCADE)
    trade_type = models.CharField(max_length=4, choices=TRADE_TYPES)
    amount = models.DecimalField(
        max_digits=24, decimal_places=8)  # Amount in base currency
    price = models.DecimalField(max_digits=24, decimal_places=8)  # Entry price
    leverage = models.IntegerField(default=1)  # 1x, 5x, 10x, etc.

    take_profit = models.DecimalField(
        max_digits=24, decimal_places=8, null=True, blank=True)
    stop_loss = models.DecimalField(
        max_digits=24, decimal_places=8, null=True, blank=True)

    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='open')
    profit_calculation_mode = models.CharField(
        max_length=10, choices=PROFIT_CALCULATION_MODES, default='auto')

    # For manual profit adjustment by admin
    manual_profit = models.DecimalField(
        max_digits=24, decimal_places=8, null=True, blank=True)

    # Calculated fields
    current_profit = models.DecimalField(
        max_digits=24, decimal_places=8, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.trade_type} {self.amount} {self.market.name}"
