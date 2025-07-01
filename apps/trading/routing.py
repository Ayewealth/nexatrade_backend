from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/markets/$", consumers.MarketConsumer.as_asgi()),
    re_path(r"ws/profits/$", consumers.ProfitConsumer.as_asgi()),
]
