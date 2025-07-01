# admin_panel/models.py
from django.db import models
from apps.authentication.models import User
from apps.wallets.models import Transaction
from apps.trading.models import Trade


class AdminAction(models.Model):
    """Model to track admin actions"""
    ACTION_TYPES = [
        ('approve_deposit', 'Approve Deposit'),
        ('reject_deposit', 'Reject Deposit'),
        ('approve_withdrawal', 'Approve Withdrawal'),
        ('reject_withdrawal', 'Reject Withdrawal'),
        ('adjust_trade_profit', 'Adjust Trade Profit'),
        ('approve_kyc', 'Approve KYC'),
        ('reject_kyc', 'Reject KYC'),
    ]

    admin_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='admin_actions')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    transaction = models.ForeignKey(
        Transaction, on_delete=models.SET_NULL, null=True, blank=True)
    trade = models.ForeignKey(
        Trade, on_delete=models.SET_NULL, null=True, blank=True)
    target_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='received_admin_actions')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin_user.email} - {self.action_type} - {self.created_at}"
