from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, KYCDocument


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for custom User model with KYC fields"""

    list_display = (
        'email',
        'phone_number',
        'date_of_birth',
        'kyc_status',
        'is_active',
        'is_staff',
        'is_superuser',
        'date_joined',
    )
    list_filter = (
        'kyc_status',
        'is_active',
        'is_staff',
        'is_superuser',
    )
    search_fields = ('email', 'phone_number')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {
            'fields': ('username', 'phone_number', 'date_of_birth', 'address')
        }),
        (_('KYC verification'), {'fields': ('kyc_status',)}),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'phone_number'),
        }),
    )

    readonly_fields = ('date_joined', 'last_login')


@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    """Admin configuration for KYC documents"""

    list_display = ('user', 'document_type', 'uploaded_at')
    list_filter = ('document_type',)
    search_fields = ('user__email', 'user__phone_number')
    readonly_fields = ('uploaded_at',)
