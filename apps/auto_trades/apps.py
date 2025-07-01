from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError


class AutoTradesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.auto_trades"

    def ready(self):
        import apps.auto_trades.signals
        try:
            from .tasks import create_auto_trades_task, close_scheduled_auto_trades_task, finalize_expired_subscriptions_task
            create_auto_trades_task()
            close_scheduled_auto_trades_task()
            finalize_expired_subscriptions_task()
        except (OperationalError, ProgrammingError):
            # This means tables aren't ready yet, so skip for now
            pass
