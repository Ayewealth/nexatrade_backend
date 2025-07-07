import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .serializers import ChatMessageSerializer
from django.contrib.auth.models import AnonymousUser


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"
        user = self.scope.get("user")

        if not user or not user.is_authenticated or user == AnonymousUser():
            await self.close()
            return

        self.user = user
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get("type", "message")
        user = self.scope["user"]

        if user == AnonymousUser():
            return

        if message_type == "message":
            message = data.get("message")
            if not message:
                return

            chat_message = await self.save_message(user, message)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": chat_message,
                }
            )

        elif message_type == "typing":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_indicator",
                    "user_id": user.id,
                    "user_name": user.get_full_name() or user.email,
                    "is_typing": True,
                }
            )

        elif message_type == "stop_typing":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_indicator",
                    "user_id": user.id,
                    "user_name": user.get_full_name() or user.email,
                    "is_typing": False,
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            "type": "typing" if event["is_typing"] else "stop_typing",
            "user_id": event["user_id"],
            "user_name": event["user_name"],
        }))

    @database_sync_to_async
    def save_message(self, user, message):
        # ✅ Import here, after Django setup is guaranteed
        from .models import ChatConversation, ChatMessage

        conversation = ChatConversation.objects.get(id=self.conversation_id)
        msg = ChatMessage.objects.create(
            conversation=conversation,
            sender=user,
            message=message
        )
        return ChatMessageSerializer(msg).data
