from django.contrib import admin
from .models import AdminAction


@admin.register(AdminAction)
class AdminActionAdmin(admin.ModelAdmin):
    """Admin view for AdminAction"""
    list_display = (
        'admin_email', 'action_type', 'target_email',
        'transaction_display', 'trade_display', 'created_at'
    )
    list_filter = ('action_type', 'created_at')
    search_fields = (
        'admin_user__email', 'target_user__email',
        'transaction__id', 'trade__id'
    )
    readonly_fields = ('created_at',)

    def admin_email(self, obj):
        return obj.admin_user.email
    admin_email.short_description = "Admin Email"

    def target_email(self, obj):
        return obj.target_user.email
    target_email.short_description = "Target User Email"

    def transaction_display(self, obj):
        return f"#{obj.transaction.id}" if obj.transaction else "-"
    transaction_display.short_description = "Transaction"

    def trade_display(self, obj):
        return f"#{obj.trade.id}" if obj.trade else "-"
    trade_display.short_description = "Trade"
