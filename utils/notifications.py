from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()


def notify_admins(subject: str, message: str):
    admin_emails = list(User.objects.filter(
        is_staff=True, is_active=True, is_superuser=True).values_list('email', flat=True))
    if not admin_emails:
        return
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list="nexatrade.info@gmail.com",
        fail_silently=False,
    )
