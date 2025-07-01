# wallets/serializers.py
from rest_framework import serializers
from .models import CryptoWallet, USDWallet, Transaction, CryptoType
from apps.authentication.serializers import *


class CryptoTypeSerializer(serializers.ModelSerializer):
    """Serializer for cryptocurrency types"""
    class Meta:
        model = CryptoType
        fields = ('id', 'name', 'symbol', 'logo_url', 'is_active')


class CryptoWalletSerializer(serializers.ModelSerializer):
    """Serializer for crypto wallets"""
    crypto_type = CryptoTypeSerializer(read_only=True)

    class Meta:
        model = CryptoWallet
        fields = ('id', 'user', 'crypto_type', 'wallet_address',
                  'balance', 'is_active', 'created_at')
        read_only_fields = ('id', 'user', 'wallet_address',
                            'balance', 'created_at')


class USDWalletSerializer(serializers.ModelSerializer):
    """Serializer for USD wallets"""
    class Meta:
        model = USDWallet
        fields = ('id', 'user', 'balance', 'is_active', 'created_at')
        read_only_fields = ('id', 'user', 'balance', 'created_at')


class CryptoToUSDConversionSerializer(serializers.Serializer):
    crypto_wallet = serializers.PrimaryKeyRelatedField(
        queryset=CryptoWallet.objects.all())
    amount = serializers.DecimalField(
        max_digits=24, decimal_places=8, min_value=0.00000001)


class USDToCryptoConversionSerializer(serializers.Serializer):
    crypto_wallet = serializers.PrimaryKeyRelatedField(
        queryset=CryptoWallet.objects.all())
    usd_amount = serializers.DecimalField(
        max_digits=24, decimal_places=8, min_value=0.00000001)


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for transactions"""
    crypto_wallet = serializers.SerializerMethodField()
    user = UserSerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = ('id', 'user', 'transaction_type', 'crypto_wallet', 'usd_wallet',
                  'amount', 'status', 'external_address',
                  'created_at', 'updated_at', 'notes')
        read_only_fields = ('id', 'user', 'status', 'created_at', 'updated_at')

    def get_crypto_wallet(self, obj):
        if obj.crypto_wallet:
            return obj.crypto_wallet.crypto_type.name
        return None


class DepositRequestSerializer(serializers.Serializer):
    """Serializer for deposit requests"""
    crypto_wallet = serializers.PrimaryKeyRelatedField(
        queryset=CryptoWallet.objects.all())
    amount = serializers.DecimalField(
        max_digits=24, decimal_places=8, min_value=0.00000001)
    external_address = serializers.CharField(required=False, allow_blank=True)


class WithdrawalRequestSerializer(serializers.Serializer):
    """Serializer for withdrawal requests"""
    crypto_wallet = serializers.PrimaryKeyRelatedField(
        queryset=CryptoWallet.objects.all())
    amount = serializers.DecimalField(
        max_digits=24, decimal_places=8, min_value=0.00000001)
    external_address = serializers.CharField(required=False, allow_blank=True)


class ConversionRequestSerializer(serializers.Serializer):
    """Serializer for conversion requests"""
    crypto_wallet = serializers.PrimaryKeyRelatedField(
        queryset=CryptoWallet.objects.all())
    amount = serializers.DecimalField(
        max_digits=24, decimal_places=8, min_value=0.00000001)

    def validate_crypto_wallet(self, value):
        """Ensure the crypto wallet is active"""
        if not value.is_active:
            raise serializers.ValidationError("This wallet is not active")
        return value
