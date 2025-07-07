# admin_panel/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from apps.authentication.models import User, KYCDocument
from apps.wallets.models import Transaction, CryptoWallet, USDWallet
from apps.trading.models import Trade
from apps.auto_trades.models import PackageSubscription
from .models import AdminAction
from .permissions import IsAdminUser
from .serializers import (
    AdminActionSerializer, ApproveDepositSerializer,
    ApproveWithdrawalSerializer, ManualProfitAdjustmentSerializer,
    KYCApprovalSerializer
)
from drf_yasg.utils import swagger_auto_schema


class AdminActionViewSet(viewsets.ModelViewSet):
    """ViewSet for admin actions"""
    serializer_class = AdminActionSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        # Prevent schema generation crash
        if getattr(self, 'swagger_fake_view', False):
            return AdminAction.objects.none()

        user = self.request.user
        if not user or not user.is_authenticated:
            return AdminAction.objects.none()

        return AdminAction.objects.all()

    def perform_create(self, serializer):
        """Set admin user when creating an action"""
        serializer.save(admin_user=self.request.user)


class AdminOperationsViewSet(viewsets.GenericViewSet):
    """ViewSet for admin operations"""
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(method='post', request_body=ApproveDepositSerializer)
    @action(detail=False, methods=['post'])
    def approve_deposit(self, request):
        """Approve a pending deposit"""
        serializer = ApproveDepositSerializer(data=request.data)
        if serializer.is_valid():
            transaction = serializer.validated_data['transaction']

            # Check if transaction is a pending deposit
            if transaction.transaction_type != 'deposit' or transaction.status != 'pending':
                return Response(
                    {'error': 'Transaction is not a pending deposit'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update transaction status
            transaction.status = 'approved'
            transaction.save()

            # Add funds to user's wallet
            if transaction.crypto_wallet:
                wallet = transaction.crypto_wallet
                wallet.balance += transaction.amount
                wallet.save()
            elif transaction.usd_wallet:
                wallet = transaction.usd_wallet
                wallet.balance += transaction.amount
                wallet.save()

            # Record admin action
            AdminAction.objects.create(
                admin_user=request.user,
                action_type='approve_deposit',
                transaction=transaction,
                target_user=transaction.user,
                notes=serializer.validated_data.get('notes')
            )

            return Response({'message': 'Deposit approved successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(method='post', request_body=ApproveDepositSerializer)
    @action(detail=False, methods=['post'])
    def reject_deposit(self, request):
        """Reject a pending deposit"""
        serializer = ApproveDepositSerializer(data=request.data)
        if serializer.is_valid():
            transaction = serializer.validated_data['transaction']

            # Check if transaction is a pending deposit
            if transaction.transaction_type != 'deposit' or transaction.status != 'pending':
                return Response(
                    {'error': 'Transaction is not a pending deposit'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update transaction status
            transaction.status = 'rejected'
            transaction.save()

            # Record admin action
            AdminAction.objects.create(
                admin_user=request.user,
                action_type='reject_deposit',
                transaction=transaction,
                target_user=transaction.user,
                notes=serializer.validated_data.get('notes')
            )

            return Response({'message': 'Deposit rejected successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(method='post', request_body=ApproveWithdrawalSerializer)
    @action(detail=False, methods=['post'])
    def approve_withdrawal(self, request):
        """Approve a pending withdrawal"""
        serializer = ApproveWithdrawalSerializer(data=request.data)
        if serializer.is_valid():
            transaction = serializer.validated_data['transaction']
            tx_hash = serializer.validated_data.get('tx_hash')

            # Check if transaction is a pending withdrawal
            if transaction.transaction_type != 'withdrawal' or transaction.status != 'pending':
                return Response(
                    {'error': 'Transaction is not a pending withdrawal'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update transaction status and hash
            transaction.status = 'approved'
            if tx_hash:
                transaction.tx_hash = tx_hash
            transaction.save()

            # Remove funds to user's wallet
            if transaction.crypto_wallet:
                wallet = transaction.crypto_wallet
                wallet.balance -= transaction.amount
                wallet.save()

            # Record admin action
            AdminAction.objects.create(
                admin_user=request.user,
                action_type='approve_withdrawal',
                transaction=transaction,
                target_user=transaction.user,
                notes=serializer.validated_data.get('notes')
            )

            return Response({'message': 'Withdrawal approved successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(method='post', request_body=ApproveWithdrawalSerializer)
    @action(detail=False, methods=['post'])
    def reject_withdrawal(self, request):
        """Reject a pending withdrawal"""
        serializer = ApproveWithdrawalSerializer(data=request.data)
        if serializer.is_valid():
            transaction = serializer.validated_data['transaction']

            # Check if transaction is a pending withdrawal
            if transaction.transaction_type != 'withdrawal' or transaction.status != 'pending':
                return Response(
                    {'error': 'Transaction is not a pending withdrawal'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update transaction status
            transaction.status = 'rejected'
            transaction.save()

            # Record admin action
            AdminAction.objects.create(
                admin_user=request.user,
                action_type='reject_withdrawal',
                transaction=transaction,
                target_user=transaction.user,
                notes=serializer.validated_data.get('notes')
            )

            return Response({'message': 'Withdrawal rejected successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(method='post', request_body=ManualProfitAdjustmentSerializer)
    @action(detail=False, methods=['post'])
    def adjust_trade_profit(self, request):
        """Manually adjust profit for a trade"""
        serializer = ManualProfitAdjustmentSerializer(data=request.data)
        if serializer.is_valid():
            trade = serializer.validated_data['trade']
            manual_profit = serializer.validated_data['manual_profit']

            # Check if trade is open
            if trade.status != 'open':
                return Response(
                    {'error': 'Can only adjust profit for open trades'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update trade
            trade.profit_calculation_mode = 'manual'
            trade.manual_profit = manual_profit
            trade.current_profit = manual_profit
            trade.save()

            # Record admin action
            AdminAction.objects.create(
                admin_user=request.user,
                action_type='adjust_trade_profit',
                trade=trade,
                target_user=trade.user,
                notes=serializer.validated_data.get('notes')
            )

            return Response({'message': 'Trade profit adjusted successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(method='post', request_body=KYCApprovalSerializer)
    @action(detail=False, methods=['post'])
    def approve_kyc(self, request):
        """Approve user KYC verification"""
        serializer = KYCApprovalSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Check if user's KYC is pending
            if user.kyc_status != 'pending':
                return Response(
                    {'error': 'User KYC is not pending'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update user KYC status
            user.kyc_status = 'approved'
            user.save()

            # Record admin action
            AdminAction.objects.create(
                admin_user=request.user,
                action_type='approve_kyc',
                target_user=user,
                notes=serializer.validated_data.get('notes')
            )

            return Response({'message': 'KYC approved successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(method='post', request_body=KYCApprovalSerializer)
    @action(detail=False, methods=['post'])
    def reject_kyc(self, request):
        """Reject user KYC verification"""
        serializer = KYCApprovalSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Check if user's KYC is pending
            if user.kyc_status != 'pending':
                return Response(
                    {'error': 'User KYC is not pending'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update user KYC status
            user.kyc_status = 'rejected'
            user.save()

            # Record admin action
            AdminAction.objects.create(
                admin_user=request.user,
                action_type='reject_kyc',
                target_user=user,
                notes=serializer.validated_data.get('notes')
            )

            return Response({'message': 'KYC rejected successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
