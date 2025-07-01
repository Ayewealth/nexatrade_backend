from rest_framework import serializers
from .models import TradingPackage, PackageSubscription, AutoTrade
from apps.trading.serializers import TradeSerializer


class TradingPackageSerializer(serializers.ModelSerializer):
    """Serializer for trading packages"""
    preferred_markets = serializers.StringRelatedField(
        many=True, read_only=True)

    class Meta:
        model = TradingPackage
        fields = ('id', 'name', 'description', 'min_investment', 'max_investment',
                  'duration_days', 'profit_percentage', 'is_active', 'risk_level', 'features',
                  'max_trades_per_day', 'trade_frequency_hours', 'preferred_markets')


class AutoTradeSerializer(serializers.ModelSerializer):
    """Serializer for auto-trades"""
    trade = TradeSerializer(read_only=True)

    class Meta:
        model = AutoTrade
        fields = ('id', 'trade', 'created_at')


class PackageSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for package subscriptions"""
    package = TradingPackageSerializer(read_only=True)
    auto_trades = AutoTradeSerializer(many=True, read_only=True)
    profit_progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = PackageSubscription
        fields = ('id', 'user', 'package', 'investment_amount', 'expected_profit',
                  'total_profit_earned', 'profit_progress_percentage', 'status',
                  'start_date', 'end_date', 'is_auto_trading_active', 'auto_trades')
        read_only_fields = ('id', 'user', 'expected_profit', 'start_date', 'end_date',
                            'total_profit_earned')

    def get_profit_progress_percentage(self, obj):
        return float(obj.get_profit_progress_percentage())


class SubscribePackageSerializer(serializers.Serializer):
    """Serializer for subscribing to packages"""
    package = serializers.PrimaryKeyRelatedField(
        queryset=TradingPackage.objects.filter(is_active=True))
    investment_amount = serializers.DecimalField(
        max_digits=24, decimal_places=8, min_value=0.01)
