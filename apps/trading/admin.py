from django.contrib import admin
from .models import Market, Trade


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    """Admin configuration for Market model"""
    list_display = ('name', 'base_currency', 'quote_currency',
                    'current_price', 'min_trade_amount', 'is_active')
    list_filter = ('is_active', 'base_currency', 'quote_currency')
    search_fields = ('name', 'base_currency__name', 'quote_currency')
    ordering = ('name',)
    readonly_fields = ()  # No readonly fields unless you want to prevent editing price


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    """Admin configuration for Trade model"""
    list_display = (
        'user_email', 'market', 'trade_type', 'amount', 'price',
        'leverage', 'status', 'profit_calculation_mode', 'current_profit',
        'created_at', 'closed_at'
    )
    list_filter = ('trade_type', 'status', 'market',
                   'profit_calculation_mode', 'created_at', 'closed_at')
    search_fields = ('user__email', 'market__name')
    readonly_fields = ('created_at', 'closed_at', 'current_profit')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User Email"
