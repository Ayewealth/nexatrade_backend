from channels.routing import ProtocolTypeRouter, URLRouter
from apps.support.middleware import JWTAuthMiddleware
import apps.trading.routing
import apps.support.routing


application = ProtocolTypeRouter({
    "websocket": JWTAuthMiddleware(
        URLRouter(
            apps.trading.routing.websocket_urlpatterns
            + apps.support.routing.websocket_urlpatterns
        )
    ),
})
