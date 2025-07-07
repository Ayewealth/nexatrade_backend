# serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ChatConversation, ChatMessage
from apps.authentication.serializers import UserSerializer


class ChatMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'conversation', 'sender',
                  'message', 'is_admin', 'is_read', 'created_at']
        read_only_fields = ['id', 'sender', 'is_admin', 'created_at']


class ChatConversationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    admin = UserSerializer(read_only=True)
    messages = ChatMessageSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatConversation
        fields = [
            'id', 'user', 'admin', 'subject', 'status', 'created_at',
            'updated_at', 'last_message_at', 'unread_count_user',
            'unread_count_admin', 'messages', 'last_message'
        ]
        read_only_fields = ['id', 'user', 'admin',
                            'created_at', 'updated_at', 'last_message_at']

    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return ChatMessageSerializer(last_message).data
        return None


class ChatConversationListSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    admin = UserSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatConversation
        fields = [
            'id', 'user', 'admin', 'subject', 'status', 'created_at',
            'last_message_at', 'unread_count_user', 'unread_count_admin', 'last_message'
        ]

    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return {
                'message': last_message.message,
                'sender': last_message.sender.email,
                'is_admin': last_message.is_admin,
                'created_at': last_message.created_at
            }
        return None
