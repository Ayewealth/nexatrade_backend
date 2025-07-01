from django.urls import path, include

urlpatterns = [
    path('auth/', include('apps.authentication.urls')),
    path('wallet/', include('apps.wallets.urls')),
    path('trading/', include('apps.trading.urls')),
    path('auto_trades/', include('apps.auto_trades.urls')),
    path('admin_panel/', include('apps.admin_panel.urls'))
]
