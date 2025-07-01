from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CryptoWalletViewSet, USDWalletViewSet, TransactionViewSet

router = DefaultRouter()
router.register(r'crypto-wallets', CryptoWalletViewSet,
                basename='crypto-wallet')
router.register(r'usd-wallets', USDWalletViewSet, basename='usd-wallet')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
]
