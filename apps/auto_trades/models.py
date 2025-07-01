# auto_trades/models.py
from django.db import models
from apps.authentication.models import User
from apps.trading.models import *
import json
from decimal import Decimal
from django.utils import timezone


class TradingPackage(models.Model):
    """Auto-trading package model"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    min_investment = models.DecimalField(max_digits=24, decimal_places=8)
    max_investment = models.DecimalField(max_digits=24, decimal_places=8)
    duration_days = models.IntegerField()  # Package duration in days
    profit_percentage = models.DecimalField(
        max_digits=5, decimal_places=2)  # Expected profit %
    is_active = models.BooleanField(default=True)
    risk_level = models.CharField(max_length=50, null=True, blank=True)
    features = models.TextField(null=True, blank=True)
    max_trades_per_day = models.IntegerField(default=5)
    min_trade_amount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=10.00)  # % of investment
    max_trade_amount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=30.00)  # % of investment
    preferred_markets = models.ManyToManyField(
        'trading.Market', blank=True,
        help_text="Preferred markets for auto-trading. If empty, uses all active markets"
    )
    trade_frequency_hours = models.IntegerField(
        default=4, help_text="Minimum hours between trades"
    )

    def get_preferred_markets(self):
        """Get preferred markets or all active markets if none specified"""
        if self.preferred_markets.exists():
            return self.preferred_markets.filter(is_active=True)
        return Market.objects.filter(is_active=True)

    def set_features(self, feature_list):
        self.features = json.dumps(feature_list)

    def get_features(self):
        return json.loads(self.features or "[]")

    def __str__(self):
        return self.name


class AutoTrade(models.Model):
    """Model to track automatically generated trades"""
    subscription = models.ForeignKey(
        'PackageSubscription', on_delete=models.CASCADE,
        related_name='auto_trades'
    )
    trade = models.OneToOneField(
        'trading.Trade', on_delete=models.CASCADE,
        related_name='auto_trade_info'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"AutoTrade for {self.subscription} - {self.trade}"


class PackageSubscription(models.Model):
    """User subscription to auto-trading package"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='package_subscriptions')
    package = models.ForeignKey(TradingPackage, on_delete=models.CASCADE)
    investment_amount = models.DecimalField(max_digits=24, decimal_places=8)
    expected_profit = models.DecimalField(max_digits=24, decimal_places=8)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='active')

    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    total_profit_earned = models.DecimalField(
        max_digits=24, decimal_places=8, default=0
    )
    last_trade_time = models.DateTimeField(null=True, blank=True)
    is_auto_trading_active = models.BooleanField(default=True)

    def get_profit_progress_percentage(self):
        """Calculate what percentage of expected profit has been achieved"""
        if self.expected_profit == 0:
            return 100
        return min((self.total_profit_earned / self.expected_profit) * 100, 100)

    def should_create_new_trade(self):
        """Check if a new auto-trade should be created"""
        if not self.is_auto_trading_active or self.status != 'active':
            return False

        # Check if package has expired
        if timezone.now() > self.end_date:
            return False

        # Check if profit target is already achieved
        if self.total_profit_earned >= self.expected_profit:
            return False

        # Check time since last trade
        if self.last_trade_time:
            hours_since_last = (
                timezone.now() - self.last_trade_time).total_seconds() / 3600
            if hours_since_last < self.package.trade_frequency_hours:
                return False

        # Check daily trade limit
        today_trades = self.auto_trades.filter(
            created_at__date=timezone.now().date()
        ).count()
        if today_trades >= self.package.max_trades_per_day:
            return False

        return True

    def __str__(self):
        return f"{self.user.email} - {self.package.name}"
