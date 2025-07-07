# auto_trades/views.py
# auto_trades/views.py (updated)
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .models import TradingPackage, PackageSubscription, AutoTrade
from apps.wallets.models import USDWallet
from .serializers import (
    TradingPackageSerializer, PackageSubscriptionSerializer,
    SubscribePackageSerializer, AutoTradeSerializer
)
from .services import AutoTradingService
from utils.notifications import notify_admins


class TradingPackageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for trading packages - read only for users"""
    queryset = TradingPackage.objects.filter(is_active=True)
    serializer_class = TradingPackageSerializer
    permission_classes = [permissions.IsAuthenticated]


class PackageSubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = PackageSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Only allow users to see their own subscriptions"""
        if getattr(self, 'swagger_fake_view', False):
            return PackageSubscription.objects.none()

        user = self.request.user
        if not user or not user.is_authenticated:
            return PackageSubscription.objects.none()

        if user.is_staff:
            return PackageSubscription.objects.all()
        return PackageSubscription.objects.filter(user=user)

    @action(detail=False, methods=['post'])
    def subscribe(self, request):
        """Subscribe to an auto-trading package"""
        serializer = SubscribePackageSerializer(data=request.data)
        if serializer.is_valid():
            package = serializer.validated_data['package']
            investment_amount = serializer.validated_data['investment_amount']

            # Check investment limits
            if investment_amount < package.min_investment or investment_amount > package.max_investment:
                return Response({
                    'error': f'Investment amount must be between {package.min_investment} and {package.max_investment}'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get or create USD wallet
            usd_wallet, created = USDWallet.objects.get_or_create(
                user=request.user,
                defaults={'balance': 0}
            )

            # Check if user has enough balance
            if usd_wallet.balance < investment_amount:
                return Response(
                    {'error': 'Insufficient USD balance'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Calculate expected profit
            expected_profit = investment_amount * \
                (package.profit_percentage / 100)

            # Calculate end date
            end_date = timezone.now() + timedelta(days=package.duration_days)

            # Create subscription
            subscription = PackageSubscription.objects.create(
                user=request.user,
                package=package,
                investment_amount=investment_amount,
                expected_profit=expected_profit,
                end_date=end_date,
                status='active',
                is_auto_trading_active=True
            )

            # Reduce wallet balance
            usd_wallet.balance -= investment_amount
            usd_wallet.save()

            # Immediately try to create first auto-trade
            AutoTradingService.create_auto_trade(subscription)

            notify_admins(
                subject="New Investment Subscription",
                message=(
                    f"User {request.user.email} subscribed to package '{package.name}' "
                    f"with investment amount {investment_amount} USD."
                )
            )

            return Response(
                PackageSubscriptionSerializer(subscription).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def toggle_auto_trading(self, request, pk=None):
        """Toggle auto-trading on/off for a subscription"""
        subscription = self.get_object()

        if subscription.status != 'active':
            return Response(
                {'error': 'Can only toggle auto-trading for active subscriptions'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription.is_auto_trading_active = not subscription.is_auto_trading_active
        subscription.save()

        return Response({
            'message': f'Auto-trading {"enabled" if subscription.is_auto_trading_active else "disabled"}',
            'is_auto_trading_active': subscription.is_auto_trading_active
        })

    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Get detailed performance metrics for a subscription"""
        subscription = self.get_object()

        # Calculate performance metrics
        auto_trades = subscription.auto_trades.all()
        closed_trades = [
            at.trade for at in auto_trades if at.trade.status == 'closed']

        total_trades = len(closed_trades)
        profitable_trades = len(
            [t for t in closed_trades if t.current_profit > 0])
        win_rate = (profitable_trades / total_trades *
                    100) if total_trades > 0 else 0

        # Calculate days remaining
        days_remaining = max(0, (subscription.end_date - timezone.now()).days)

        return Response({
            'total_trades': total_trades,
            'profitable_trades': profitable_trades,
            'win_rate': round(win_rate, 2),
            'total_profit_earned': subscription.total_profit_earned,
            'expected_profit': subscription.expected_profit,
            'profit_progress': subscription.get_profit_progress_percentage(),
            'days_remaining': days_remaining,
            'is_auto_trading_active': subscription.is_auto_trading_active
        })


class AutoTradeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing auto-trades"""
    serializer_class = AutoTradeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Only allow users to see their own auto-trades"""
        if getattr(self, 'swagger_fake_view', False):
            return AutoTrade.objects.none()

        user = self.request.user
        if not user or not user.is_authenticated:
            return AutoTrade.objects.none()

        if user.is_staff:
            return AutoTrade.objects.all()
        return AutoTrade.objects.filter(subscription__user=user)
