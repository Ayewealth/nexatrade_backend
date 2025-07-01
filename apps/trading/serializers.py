# trading/serializers.py
from rest_framework import serializers
from .models import Market, Trade
from apps.wallets.serializers import *
from apps.authentication.serializers import *


class MarketSerializer(serializers.ModelSerializer):
    """Serializer for markets"""
    base_currency = CryptoTypeSerializer(read_only=True)

    class Meta:
        model = Market
        fields = ('id', 'name', 'base_currency', 'quote_currency',
                  'is_active', 'current_price', 'min_trade_amount')


class TradeSerializer(serializers.ModelSerializer):
    """Serializer for trades"""
    market = MarketSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Trade
        fields = ('id', 'user', 'market', 'trade_type', 'amount', 'price',
                  'leverage', 'take_profit', 'stop_loss', 'status',
                  'profit_calculation_mode', 'current_profit',
                  'created_at', 'closed_at')
        read_only_fields = ('id', 'user', 'price', 'status', 'profit_calculation_mode',
                            'current_profit', 'created_at', 'closed_at')


class CreateTradeSerializer(serializers.Serializer):
    """Serializer for creating trades"""
    market = serializers.PrimaryKeyRelatedField(
        queryset=Market.objects.filter(is_active=True))
    trade_type = serializers.ChoiceField(choices=Trade.TRADE_TYPES)
    amount = serializers.DecimalField(
        max_digits=24, decimal_places=8, min_value=0.00000001)
    leverage = serializers.IntegerField(default=1, min_value=1, max_value=100)
    take_profit = serializers.DecimalField(
        max_digits=24, decimal_places=8, required=False)
    stop_loss = serializers.DecimalField(
        max_digits=24, decimal_places=8, required=False)
