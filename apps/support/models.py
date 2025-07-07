# models.py
from django.db import models
from apps.authentication.models import User
from django.utils import timezone


class ChatConversation(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='chat_conversations')
    admin = models.ForeignKey(User, on_delete=models.SET_NULL,
                              null=True, blank=True, related_name='admin_conversations')
    subject = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('pending', 'Pending')
    ], default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    unread_count_user = models.IntegerField(default=0)
    unread_count_admin = models.IntegerField(default=0)

    class Meta:
        ordering = ['-last_message_at', '-created_at']

    def __str__(self):
        return f"Chat: {self.user.email} - {self.subject or 'No Subject'}"


class ChatMessage(models.Model):
    conversation = models.ForeignKey(
        ChatConversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_admin = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        # Set is_admin based on user permissions
        if self.sender and self.sender.is_staff:
            self.is_admin = True

        super().save(*args, **kwargs)

        # Update conversation's last_message_at and unread counts
        conversation = self.conversation
        conversation.last_message_at = self.created_at

        if self.is_admin:
            conversation.unread_count_user += 1
            conversation.unread_count_admin = 0
        else:
            conversation.unread_count_admin += 1
            conversation.unread_count_user = 0

        conversation.save()

    def __str__(self):
        return f"{self.sender.email}: {self.message[:50]}..."
