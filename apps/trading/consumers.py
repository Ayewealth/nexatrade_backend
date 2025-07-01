import json
from channels.generic.websocket import AsyncWebsocketConsumer


class MarketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("markets", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("markets", self.channel_name)

    async def market_update(self, event):
        # Send updated market price to WebSocket
        await self.send(text_data=json.dumps(event["data"]))


class ProfitConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("profits", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("profits", self.channel_name)

    async def profit_update(self, event):
        await self.send(text_data=json.dumps(event["data"]))
