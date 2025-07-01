# wallets/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CryptoWallet, USDWallet, Transaction
from apps.trading.models import Market
from .serializers import *

from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg.utils import swagger_auto_schema
from decimal import Decimal
import requests


class CryptoWalletViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for crypto wallets - read only for users"""
    serializer_class = CryptoWalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Only allow users to see their own wallets"""
        if self.request.user.is_staff:
            return CryptoWallet.objects.all()
        return CryptoWallet.objects.filter(user=self.request.user)


class USDWalletViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for USD wallets - read only for users"""
    serializer_class = USDWalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Only allow users to see their own wallets"""
        # if self.request.user.is_staff:
        #     return USDWallet.objects.all()
        return USDWallet.objects.filter(user=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    """ViewSet for transaction operations"""
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Only allow users to see their own transactions"""
        if getattr(self, 'swagger_fake_view', False):
            return Transaction.objects.none()

        if self.request.user.is_staff:
            return Transaction.objects.all()
        return Transaction.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Set user when creating a transaction"""
        serializer.save(user=self.request.user)

    def get_crypto_price(self, crypto_type):
        """Get current price of cryptocurrency in USD"""
        try:
            if crypto_type.coingecko_id:
                # Using CoinGecko API
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_type.coingecko_id}&vs_currencies=usd"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return Decimal(str(data[crypto_type.coingecko_id]['usd']))

            elif crypto_type.coinpaprika_id:
                # Using CoinPaprika API as fallback
                url = f"https://api.coinpaprika.com/v1/tickers/{crypto_type.coinpaprika_id}"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return Decimal(str(data['quotes']['USD']['price']))

            # Fallback: return a default price or raise an error
            raise ValueError("No price data available")

        except Exception as e:
            # In production, you might want to log this error
            raise ValueError(
                f"Failed to get price for {crypto_type.symbol}: {str(e)}")

    @swagger_auto_schema(method='post', request_body=DepositRequestSerializer)
    @action(detail=False, methods=['post'])
    def deposit(self, request):
        """Create a deposit request"""
        serializer = DepositRequestSerializer(data=request.data)
        if serializer.is_valid():
            crypto_wallet = serializer.validated_data['crypto_wallet']

            # Check if the wallet belongs to the user
            if crypto_wallet.user != request.user:
                return Response(
                    {'error': 'This wallet does not belong to you'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Create pending deposit transaction
            transaction = Transaction.objects.create(
                user=request.user,
                transaction_type='deposit',
                crypto_wallet=crypto_wallet,
                amount=serializer.validated_data['amount'],
                status='pending',
                external_address=serializer.validated_data.get(
                    'external_address'),
            )

            return Response(
                TransactionSerializer(transaction).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(method='post', request_body=WithdrawalRequestSerializer)
    @action(detail=False, methods=['post'])
    def withdraw(self, request):
        """Create a withdrawal request"""
        serializer = WithdrawalRequestSerializer(data=request.data)
        if serializer.is_valid():
            crypto_wallet = serializer.validated_data['crypto_wallet']
            amount = serializer.validated_data['amount']
            external_address = serializer.validated_data['external_address']

            # Check if the wallet belongs to the user
            if crypto_wallet.user != request.user:
                return Response(
                    {'error': 'This wallet does not belong to you'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Check if user has enough balance
            if crypto_wallet.balance < amount:
                return Response(
                    {'error': 'Insufficient balance'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create pending withdrawal transaction
            transaction = Transaction.objects.create(
                user=request.user,
                transaction_type='withdrawal',
                crypto_wallet=crypto_wallet,
                amount=amount,
                status='pending',
                external_address=external_address
            )

            return Response(
                TransactionSerializer(transaction).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(method='post', request_body=ConversionRequestSerializer)
    @action(detail=False, methods=['post'], url_path='convert-to-usd')
    def convert_to_usd(self, request):
        """Convert cryptocurrency to USD wallet"""
        serializer = ConversionRequestSerializer(data=request.data)
        if serializer.is_valid():
            crypto_wallet = serializer.validated_data['crypto_wallet']
            amount = serializer.validated_data['amount']

            # Check if the wallet belongs to the user
            if crypto_wallet.user != request.user:
                return Response(
                    {'error': 'This wallet does not belong to you'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Check if user has enough balance
            if crypto_wallet.balance < amount:
                return Response(
                    {'error': 'Insufficient balance in crypto wallet'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                # Get current crypto price
                crypto_price = self.get_crypto_price(crypto_wallet.crypto_type)
                usd_amount = amount * crypto_price

                # Get or create user's USD wallet
                usd_wallet, created = USDWallet.objects.get_or_create(
                    user=request.user,
                    defaults={'balance': Decimal('0')}
                )

                crypto_wallet.balance -= amount
                usd_wallet.balance += usd_amount
                crypto_wallet.save()
                usd_wallet.save()

                # Create conversion transaction
                transaction = Transaction.objects.create(
                    user=request.user,
                    transaction_type='conversion',
                    crypto_wallet=crypto_wallet,
                    usd_wallet=usd_wallet,
                    amount=amount,
                    usd_amount=usd_amount,
                    conversion_rate=crypto_price,
                    status='completed',
                )

                return Response({
                    'transaction': TransactionSerializer(transaction).data,
                    'conversion_details': {
                        'crypto_amount': amount,
                        'crypto_symbol': crypto_wallet.crypto_type.symbol,
                        'usd_amount': usd_amount,
                        'conversion_rate': crypto_price
                    }
                }, status=status.HTTP_201_CREATED)

            except ValueError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(method='post', request_body=USDToCryptoConversionSerializer)
    @action(detail=False, methods=['post'], url_path='convert-to-crypto')
    def convert_to_crypto(self, request):
        """Convert from USDWallet to CryptoWallet"""
        from apps.trading.models import Market

        serializer = USDToCryptoConversionSerializer(data=request.data)
        if serializer.is_valid():
            crypto_wallet = serializer.validated_data['crypto_wallet']
            usd_amount = serializer.validated_data['usd_amount']

            if crypto_wallet.user != request.user:
                return Response({'error': 'This wallet does not belong to you'}, status=403)

            crypto_price = self.get_crypto_price(crypto_wallet.crypto_type)

            usd_wallet, _ = USDWallet.objects.get_or_create(
                user=request.user, defaults={'balance': 0})

            if usd_wallet.balance < usd_amount:
                return Response({'error': 'Insufficient USD balance'}, status=400)

            # Convert USD → Crypto
            crypto_amount = usd_amount / crypto_price

            usd_wallet.balance -= usd_amount
            crypto_wallet.balance += crypto_amount
            usd_wallet.save()
            crypto_wallet.save()

            transaction = Transaction.objects.create(
                user=request.user,
                transaction_type='conversion',
                crypto_wallet=crypto_wallet,
                usd_wallet=usd_wallet,
                amount=usd_amount,
                status='completed',
                notes=f"Converted ${usd_amount:.2f} USD to {crypto_amount:.8f} {crypto_wallet.crypto_type.symbol}"
            )

            return Response(TransactionSerializer(transaction).data, status=201)

        return Response(serializer.errors, status=400)

    @action(detail=False, methods=['get'], url_path='wallet-usd-value')
    def get_wallet_usd_value(self, request):
        """Get USD value of a specific crypto wallet or all crypto wallets"""
        from apps.trading.models import Market

        crypto_wallet_id = request.query_params.get('crypto_wallet_id')

        if crypto_wallet_id:
            # Get USD value for a specific wallet
            try:
                crypto_wallet = CryptoWallet.objects.get(
                    id=crypto_wallet_id,
                    user=request.user
                )
            except CryptoWallet.DoesNotExist:
                return Response(
                    {'error': 'Crypto wallet not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            try:
                market = Market.objects.get(
                    base_currency=crypto_wallet.crypto_type,
                    quote_currency='USD'
                )

                usd_value = crypto_wallet.balance * market.current_price

                return Response({
                    'wallet_id': crypto_wallet.id,
                    'crypto_symbol': crypto_wallet.crypto_type.symbol,
                    'crypto_name': crypto_wallet.crypto_type.name,
                    'crypto_balance': crypto_wallet.balance,
                    'current_price_usd': market.current_price,
                    'total_usd_value': usd_value,
                    'wallet_address': crypto_wallet.wallet_address
                })

            except Market.DoesNotExist:
                return Response({
                    'wallet_id': crypto_wallet.id,
                    'crypto_symbol': crypto_wallet.crypto_type.symbol,
                    'crypto_name': crypto_wallet.crypto_type.name,
                    'crypto_balance': crypto_wallet.balance,
                    'current_price_usd': None,
                    'total_usd_value': None,
                    'error': 'Market data not available for this cryptocurrency',
                    'wallet_address': crypto_wallet.wallet_address
                })

        else:
            # Get USD value for all user's crypto wallets
            crypto_wallets = CryptoWallet.objects.filter(
                user=request.user,
                is_active=True
            )

            wallet_values = []
            total_portfolio_value = 0

            for wallet in crypto_wallets:
                try:
                    market = Market.objects.get(
                        base_currency=wallet.crypto_type,
                        quote_currency='USD'
                    )

                    usd_value = wallet.balance * market.current_price
                    total_portfolio_value += usd_value

                    wallet_data = {
                        'wallet_id': wallet.id,
                        'crypto_symbol': wallet.crypto_type.symbol,
                        'crypto_name': wallet.crypto_type.name,
                        'crypto_balance': wallet.balance,
                        'current_price_usd': market.current_price,
                        'total_usd_value': usd_value,
                        'wallet_address': wallet.wallet_address,
                        'market_available': True
                    }

                except Market.DoesNotExist:
                    wallet_data = {
                        'wallet_id': wallet.id,
                        'crypto_symbol': wallet.crypto_type.symbol,
                        'crypto_name': wallet.crypto_type.name,
                        'crypto_balance': wallet.balance,
                        'current_price_usd': None,
                        'total_usd_value': None,
                        'wallet_address': wallet.wallet_address,
                        'market_available': False,
                        'error': 'Market data not available'
                    }

                wallet_values.append(wallet_data)

            return Response({
                'total_wallets': len(wallet_values),
                'total_portfolio_value_usd': total_portfolio_value,
                'wallets': wallet_values
            })

    @action(detail=False, methods=['get'], url_path='portfolio-summary')
    def get_portfolio_summary(self, request):
        """Get a summary of user's entire portfolio including USD wallet"""
        from apps.trading.models import Market

        # Get USD wallet
        try:
            usd_wallet = USDWallet.objects.get(user=request.user)
            usd_balance = usd_wallet.balance
        except USDWallet.DoesNotExist:
            usd_balance = 0

        # Get all crypto wallets
        crypto_wallets = CryptoWallet.objects.filter(
            user=request.user,
            is_active=True
        )

        crypto_portfolio = []
        total_crypto_value = 0

        for wallet in crypto_wallets:
            try:
                market = Market.objects.get(
                    base_currency=wallet.crypto_type,
                    quote_currency='USD'
                )

                usd_value = wallet.balance * market.current_price
                total_crypto_value += usd_value

                percentage_of_portfolio = 0  # Will calculate after getting total

                crypto_data = {
                    'crypto_symbol': wallet.crypto_type.symbol,
                    'crypto_name': wallet.crypto_type.name,
                    'balance': wallet.balance,
                    'current_price_usd': market.current_price,
                    'usd_value': usd_value,
                    'percentage_of_crypto_portfolio': 0  # Will calculate below
                }

            except Market.DoesNotExist:
                crypto_data = {
                    'crypto_symbol': wallet.crypto_type.symbol,
                    'crypto_name': wallet.crypto_type.name,
                    'balance': wallet.balance,
                    'current_price_usd': None,
                    'usd_value': None,
                    'percentage_of_crypto_portfolio': 0,
                    'market_available': False
                }

            crypto_portfolio.append(crypto_data)

        # Calculate percentages
        total_portfolio_value = total_crypto_value + usd_balance

        for crypto in crypto_portfolio:
            if crypto.get('usd_value'):
                crypto['percentage_of_total_portfolio'] = (
                    (crypto['usd_value'] / total_portfolio_value * 100)
                    if total_portfolio_value > 0 else 0
                )
                crypto['percentage_of_crypto_portfolio'] = (
                    (crypto['usd_value'] / total_crypto_value * 100)
                    if total_crypto_value > 0 else 0
                )

        return Response({
            'portfolio_summary': {
                'total_portfolio_value_usd': total_portfolio_value,
                'usd_balance': usd_balance,
                'crypto_portfolio_value_usd': total_crypto_value,
                'usd_percentage': (usd_balance / total_portfolio_value * 100) if total_portfolio_value > 0 else 0,
                'crypto_percentage': (total_crypto_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
            },
            'usd_wallet': {
                'balance': usd_balance
            },
            'crypto_portfolio': crypto_portfolio,
            'total_crypto_wallets': len(crypto_portfolio)
        })
