# admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q
from .models import ChatConversation, ChatMessage


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('created_at', 'updated_at', 'is_admin')
    fields = ('sender', 'message', 'is_admin', 'is_read', 'created_at')

    def has_add_permission(self, request, obj=None):
        return False  # Prevent adding messages through inline


@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user_email', 'subject_display', 'admin_assigned',
        'status', 'message_count', 'unread_indicator', 'last_activity', 'created_at'
    )
    list_filter = (
        'status', 'created_at', 'last_message_at',
        ('admin', admin.EmptyFieldListFilter)
    )
    search_fields = ('user__email', 'user__first_name',
                     'user__last_name', 'subject')
    readonly_fields = ('created_at', 'updated_at',
                       'last_message_at', 'message_count_display')
    raw_id_fields = ('user', 'admin')

    fieldsets = (
        ('Conversation Info', {
            'fields': ('user', 'admin', 'subject', 'status')
        }),
        ('Counters', {
            'fields': ('unread_count_user', 'unread_count_admin')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_message_at', 'message_count_display'),
            'classes': ('collapse',)
        })
    )

    inlines = [ChatMessageInline]

    actions = ['mark_as_closed', 'mark_as_active',
               'assign_to_me', 'mark_all_read']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'admin').annotate(
            message_count=Count('messages')
        )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'

    def subject_display(self, obj):
        return obj.subject or 'No Subject'
    subject_display.short_description = 'Subject'
    subject_display.admin_order_field = 'subject'

    def admin_assigned(self, obj):
        if obj.admin:
            return obj.admin.email
        return format_html('<span style="color: red;">Unassigned</span>')
    admin_assigned.short_description = 'Admin'
    admin_assigned.admin_order_field = 'admin__email'

    def message_count(self, obj):
        return obj.message_count
    message_count.short_description = 'Messages'
    message_count.admin_order_field = 'message_count'

    def message_count_display(self, obj):
        return obj.messages.count()
    message_count_display.short_description = 'Total Messages'

    def unread_indicator(self, obj):
        indicators = []
        if obj.unread_count_user > 0:
            indicators.append(format_html(
                '<span style="background: #ff6b6b; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">U: {}</span>',
                obj.unread_count_user
            ))
        if obj.unread_count_admin > 0:
            indicators.append(format_html(
                '<span style="background: #4ecdc4; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">A: {}</span>',
                obj.unread_count_admin
            ))
        return format_html(' '.join(indicators)) if indicators else '✓'
    unread_indicator.short_description = 'Unread'

    def last_activity(self, obj):
        if obj.last_message_at:
            return obj.last_message_at.strftime('%Y-%m-%d %H:%M')
        return 'Never'
    last_activity.short_description = 'Last Activity'
    last_activity.admin_order_field = 'last_message_at'

    def mark_as_closed(self, request, queryset):
        updated = queryset.update(status='closed')
        self.message_user(
            request, f'{updated} conversations marked as closed.')
    mark_as_closed.short_description = 'Mark selected conversations as closed'

    def mark_as_active(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(
            request, f'{updated} conversations marked as active.')
    mark_as_active.short_description = 'Mark selected conversations as active'

    def assign_to_me(self, request, queryset):
        updated = queryset.update(admin=request.user)
        self.message_user(request, f'{updated} conversations assigned to you.')
    assign_to_me.short_description = 'Assign selected conversations to me'

    def mark_all_read(self, request, queryset):
        updated = queryset.update(unread_count_admin=0)
        self.message_user(
            request, f'Marked {updated} conversations as read for admins.')
    mark_all_read.short_description = 'Mark as read (admin)'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'conversation_link', 'sender_email', 'message_preview',
        'sender_type', 'is_read', 'created_at'
    )
    list_filter = (
        'is_admin', 'is_read', 'created_at',
        ('conversation__admin', admin.EmptyFieldListFilter)
    )
    search_fields = (
        'sender__email', 'sender__first_name', 'sender__last_name',
        'message', 'conversation__subject'
    )
    readonly_fields = ('created_at', 'updated_at', 'is_admin')
    raw_id_fields = ('conversation', 'sender')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Message Info', {
            'fields': ('conversation', 'sender', 'message')
        }),
        ('Status', {
            'fields': ('is_admin', 'is_read')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    actions = ['mark_as_read', 'mark_as_unread']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('conversation', 'sender', 'conversation__user')

    def conversation_link(self, obj):
        url = reverse('admin:chat_chatconversation_change',
                      args=[obj.conversation.id])
        return format_html('<a href="{}">{}</a>', url, str(obj.conversation))
    conversation_link.short_description = 'Conversation'
    conversation_link.admin_order_field = 'conversation'

    def sender_email(self, obj):
        return obj.sender.email
    sender_email.short_description = 'Sender'
    sender_email.admin_order_field = 'sender__email'

    def message_preview(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_preview.short_description = 'Message'

    def sender_type(self, obj):
        if obj.is_admin:
            return format_html('<span style="color: #28a745; font-weight: bold;">Admin</span>')
        else:
            return format_html('<span style="color: #007bff;">User</span>')
    sender_type.short_description = 'Type'
    sender_type.admin_order_field = 'is_admin'

    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} messages marked as read.')
    mark_as_read.short_description = 'Mark selected messages as read'

    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} messages marked as unread.')
    mark_as_unread.short_description = 'Mark selected messages as unread'


# Optional: Custom admin site configuration
admin.site.site_header = 'Chat Administration'
admin.site.site_title = 'Chat Admin'
admin.site.index_title = 'Welcome to Chat Administration'
