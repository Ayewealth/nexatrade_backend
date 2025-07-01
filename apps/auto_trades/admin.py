from django.contrib import admin
from .models import TradingPackage, PackageSubscription, AutoTrade


@admin.register(TradingPackage)
class TradingPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'profit_percentage', 'duration_days', 'min_investment',
                    'max_investment', 'is_active')
    list_filter = ('is_active', 'risk_level')
    search_fields = ('name', 'description')
    filter_horizontal = ('preferred_markets',)


@admin.register(PackageSubscription)
class PackageSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'package', 'investment_amount', 'total_profit_earned',
                    'status', 'start_date', 'end_date', 'is_auto_trading_active')
    list_filter = ('status', 'is_auto_trading_active', 'package')
    search_fields = ('user__email', 'package__name')
    readonly_fields = ('start_date', 'expected_profit')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'package')


@admin.register(AutoTrade)
class AutoTradeAdmin(admin.ModelAdmin):
    list_display = ('subscription', 'trade', 'created_at')
    list_filter = ('created_at', 'trade__status')
    search_fields = ('subscription__user__email',
                     'subscription__package__name')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'subscription__user', 'subscription__package', 'trade'
        )
