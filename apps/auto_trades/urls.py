from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TradingPackageViewSet, PackageSubscriptionViewSet, AutoTradeViewSet

router = DefaultRouter()
router.register(r'packages', TradingPackageViewSet)
router.register(r'subscriptions', PackageSubscriptionViewSet,
                basename='packagesubscription')
router.register(r'auto-trades', AutoTradeViewSet, basename='autotrade')

urlpatterns = [
    path('', include(router.urls)),
]
