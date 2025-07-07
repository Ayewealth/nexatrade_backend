import os
from channels.routing import ProtocolTypeRouter, URLRouter
from apps.support.middleware import JWTAuthMiddleware
from django.core.asgi import get_asgi_application

import apps.trading.routing
import apps.support.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nexatrade_backend.settings")

# Django's ASGI application to handle traditional HTTP requests
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,  # Handle HTTP requests with Django
    "websocket": JWTAuthMiddleware(
        URLRouter(
            apps.trading.routing.websocket_urlpatterns +
            apps.support.routing.websocket_urlpatterns
        )
    ),
})
