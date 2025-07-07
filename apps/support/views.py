# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.contrib.auth.models import User
from .models import ChatConversation, ChatMessage
from .serializers import (
    ChatConversationSerializer,
    ChatConversationListSerializer,
    ChatMessageSerializer
)
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class ChatConversationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            # Admin can see all conversations
            return ChatConversation.objects.all().prefetch_related('messages', 'user', 'admin')
        else:
            # Regular users can only see their own conversations
            return ChatConversation.objects.filter(user=self.request.user).prefetch_related('messages', 'user', 'admin')

    def get_serializer_class(self):
        if self.action == 'list':
            return ChatConversationListSerializer
        return ChatConversationSerializer

    def create(self, request):
        """Create a new conversation (users only)"""
        if request.user.is_staff:
            return Response(
                {'error': 'Admins cannot create conversations'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if user already has an active conversation
        existing_conversation = ChatConversation.objects.filter(
            user=request.user,
            status='active'
        ).first()

        if existing_conversation:
            serializer = self.get_serializer(existing_conversation)
            return Response(serializer.data)

        # Create new conversation
        conversation = ChatConversation.objects.create(
            user=request.user,
            subject=request.data.get('subject', ''),
            status='active'
        )

        serializer = self.get_serializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message in a conversation"""
        try:
            conversation = self.get_object()

            # Check permissions
            if not request.user.is_staff and conversation.user != request.user:
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )

            message_text = request.data.get('message', '').strip()
            if not message_text:
                return Response(
                    {'error': 'Message cannot be empty'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create message
            message = ChatMessage.objects.create(
                conversation=conversation,
                sender=request.user,
                message=message_text
            )

            # If admin is sending first message, assign them to conversation
            if request.user.is_staff and not conversation.admin:
                conversation.admin = request.user
                conversation.save()

            serializer = ChatMessageSerializer(message)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ChatConversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark messages as read"""
        try:
            conversation = self.get_object()

            # Check permissions
            if not request.user.is_staff and conversation.user != request.user:
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )

            if request.user.is_staff:
                # Admin marking as read
                conversation.unread_count_admin = 0
                conversation.messages.filter(
                    is_admin=False, is_read=False).update(is_read=True)
            else:
                # User marking as read
                conversation.unread_count_user = 0
                conversation.messages.filter(
                    is_admin=True, is_read=False).update(is_read=True)

            conversation.save()

            return Response({'status': 'success'})

        except ChatConversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update conversation status (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            conversation = self.get_object()
            new_status = request.data.get('status')

            if new_status not in ['active', 'closed', 'pending']:
                return Response(
                    {'error': 'Invalid status'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            conversation.status = new_status
            conversation.save()

            serializer = self.get_serializer(conversation)
            return Response(serializer.data)

        except ChatConversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get total unread count for current user"""
        if request.user.is_staff:
            # Admin unread count
            total_unread = ChatConversation.objects.filter(
                unread_count_admin__gt=0
            ).count()
        else:
            # User unread count
            total_unread = ChatConversation.objects.filter(
                user=request.user,
                unread_count_user__gt=0
            ).count()

        return Response({'unread_count': total_unread})


class ChatMessageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.request.query_params.get('conversation_id')
        if not conversation_id:
            return ChatMessage.objects.none()

        try:
            conversation = ChatConversation.objects.get(id=conversation_id)

            # Check permissions
            if not self.request.user.is_staff and conversation.user != self.request.user:
                return ChatMessage.objects.none()

            return ChatMessage.objects.filter(conversation=conversation)

        except ChatConversation.DoesNotExist:
            return ChatMessage.objects.none()
