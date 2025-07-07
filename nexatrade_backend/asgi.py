import apps.support.routing
import apps.trading.routing
from apps.support.middleware import JWTAuthMiddleware
import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nexatrade_backend.settings")

# Initialize Django before any model-dependent imports
django_asgi_app = get_asgi_application()

# ✅ Now it's safe to import app code

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        URLRouter(
            apps.trading.routing.websocket_urlpatterns +
            apps.support.routing.websocket_urlpatterns
        )
    ),
})
