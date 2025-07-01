# admin_panel/serializers.py
from rest_framework import serializers
from .models import AdminAction
from apps.authentication.models import User
from apps.authentication.serializers import *
from apps.wallets.models import Transaction
from apps.trading.models import Trade


class AdminActionSerializer(serializers.ModelSerializer):
    """Serializer for admin actions"""
    admin_user = UserSerializer(read_only=True)
    target_user = UserSerializer(read_only=True)

    class Meta:
        model = AdminAction
        fields = ('id', 'admin_user', 'action_type', 'transaction', 'trade',
                  'target_user', 'notes', 'created_at')
        read_only_fields = ('id', 'admin_user', 'created_at')


class ApproveDepositSerializer(serializers.Serializer):
    """Serializer for approving deposits"""
    transaction = serializers.PrimaryKeyRelatedField(
        queryset=Transaction.objects.filter(
            transaction_type='deposit', status='pending')
    )
    notes = serializers.CharField(required=False, allow_blank=True)


class ApproveWithdrawalSerializer(serializers.Serializer):
    """Serializer for approving withdrawals"""
    transaction = serializers.PrimaryKeyRelatedField(
        queryset=Transaction.objects.filter(
            transaction_type='withdrawal', status='pending')
    )
    tx_hash = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class ManualProfitAdjustmentSerializer(serializers.Serializer):
    """Serializer for adjusting trade profits manually"""
    trade = serializers.PrimaryKeyRelatedField(
        queryset=Trade.objects.filter(status='open')
    )
    manual_profit = serializers.DecimalField(max_digits=24, decimal_places=8)
    notes = serializers.CharField(required=False, allow_blank=True)


class KYCApprovalSerializer(serializers.Serializer):
    """Serializer for approving KYC"""
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(kyc_status='pending')
    )
    notes = serializers.CharField(required=False, allow_blank=True)
