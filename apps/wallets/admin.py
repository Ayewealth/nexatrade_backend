from django.contrib import admin
from .models import CryptoType, CryptoWallet, USDWallet, Transaction


@admin.register(CryptoType)
class CryptoTypeAdmin(admin.ModelAdmin):
    """Admin view for CryptoType"""
    list_display = ('name', 'symbol', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'symbol')
    ordering = ('symbol',)


@admin.register(CryptoWallet)
class CryptoWalletAdmin(admin.ModelAdmin):
    """Admin view for CryptoWallet"""
    list_display = ('user_email', 'crypto_type',
                    'wallet_address', 'balance', 'is_active')
    list_filter = ('crypto_type', 'is_active')
    search_fields = ('user__email', 'wallet_address')
    readonly_fields = ('wallet_address', 'created_at')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User Email"


@admin.register(USDWallet)
class USDWalletAdmin(admin.ModelAdmin):
    """Admin view for USDWallet"""
    list_display = ('user_email', 'balance', 'is_active', 'created_at')
    search_fields = ('user__email',)
    readonly_fields = ('created_at',)

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User Email"


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin view for Transactions"""
    list_display = (
        'user_email', 'transaction_type', 'amount',
        'status', 'crypto_wallet', 'usd_wallet', 'created_at'
    )
    list_filter = ('transaction_type', 'status', 'created_at', 'updated_at')
    search_fields = ('user__email', 'external_address')
    readonly_fields = ('created_at', 'updated_at')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User Email"
