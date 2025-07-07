# trading/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Market, Trade
from apps.wallets.models import USDWallet
from .serializers import MarketSerializer, TradeSerializer, CreateTradeSerializer
from django.utils import timezone
from utils.notifications import notify_admins


class MarketViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for markets - read only for all users"""
    queryset = Market.objects.filter(is_active=True)
    serializer_class = MarketSerializer
    permission_classes = [permissions.IsAuthenticated]


class TradeViewSet(viewsets.ModelViewSet):
    """ViewSet for trade operations"""
    serializer_class = TradeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Only allow users to see their own trades, staff can see all."""
        if getattr(self, 'swagger_fake_view', False):
            return Trade.objects.none()
        user = self.request.user
        if user.is_staff:
            return Trade.objects.all()
        return Trade.objects.filter(user=user)

    def create(self, request, *args, **kwargs):
        """Create a new trade"""
        serializer = CreateTradeSerializer(data=request.data)
        if serializer.is_valid():
            market = serializer.validated_data['market']
            trade_type = serializer.validated_data['trade_type']
            amount = serializer.validated_data['amount']
            leverage = serializer.validated_data.get('leverage', 1)

            # Get or create USD wallet for the user
            usd_wallet, created = USDWallet.objects.get_or_create(
                user=request.user,
                defaults={'balance': 0}
            )

            # Calculate required margin
            required_margin = (amount * market.current_price) / leverage

            # Check if user has enough balance
            if usd_wallet.balance < required_margin:
                return Response(
                    {'error': 'Insufficient USD balance for this trade'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create trade
            trade = Trade.objects.create(
                user=request.user,
                market=market,
                trade_type=trade_type,
                amount=amount,
                price=market.current_price,
                leverage=leverage,
                take_profit=serializer.validated_data.get('take_profit'),
                stop_loss=serializer.validated_data.get('stop_loss'),
                status='open'
            )

            # Reduce USD wallet balance
            usd_wallet.balance -= required_margin
            usd_wallet.save()

            # After usd_wallet.save() in create method:
            notify_admins(
                subject="New Trade Created",
                message=(
                    f"User {request.user.email} created a new trade.\n"
                    f"Market: {market.name}\n"
                    f"Trade Type: {trade_type}\n"
                    f"Amount: {amount}\n"
                    f"Leverage: {leverage}\n"
                    f"Price: {market.current_price}\n"
                )
            )

            return Response(
                TradeSerializer(trade).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close an open trade"""
        trade = self.get_object()

        # Only allow closing open trades
        if trade.status != 'open':
            return Response(
                {'error': 'Only open trades can be closed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Close the trade and calculate profit
        trade.status = 'closed'

        # Get current market price
        market = trade.market
        current_price = market.current_price

        # Calculate profit based on price difference
        if trade.profit_calculation_mode == 'auto':
            if trade.trade_type == 'buy':
                profit_percentage = (current_price - trade.price) / trade.price
            else:  # sell
                profit_percentage = (trade.price - current_price) / trade.price

            # Apply leverage
            profit_percentage *= trade.leverage

            # Calculate actual profit
            trade.current_profit = (
                trade.amount * trade.price) * profit_percentage

        # Use manual profit if set
        elif trade.profit_calculation_mode == 'manual' and trade.manual_profit is not None:
            trade.current_profit = trade.manual_profit

        trade.closed_at = timezone.now()
        trade.save()

        # Get or create USD wallet
        usd_wallet, created = USDWallet.objects.get_or_create(
            user=request.user,
            defaults={'balance': 0}
        )

        # Return initial margin + profit to USD wallet
        initial_margin = (trade.amount * trade.price) / trade.leverage
        usd_wallet.balance += initial_margin + trade.current_profit
        usd_wallet.save()

        return Response(TradeSerializer(trade).data)
