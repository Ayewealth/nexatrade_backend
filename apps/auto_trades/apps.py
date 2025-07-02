from django.apps import AppConfig
from django.db.models.signals import post_migrate
import logging


class AutoTradesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.auto_trades"

    def ready(self):
        from . import signals  # still safe
        post_migrate.connect(run_auto_trade_tasks, sender=self)


def run_auto_trade_tasks(sender, **kwargs):
    try:
        from .tasks import (
            create_auto_trades_task,
            close_scheduled_auto_trades_task,
            finalize_expired_subscriptions_task,
        )
        create_auto_trades_task()
        close_scheduled_auto_trades_task()
        finalize_expired_subscriptions_task()
    except Exception as e:
        logging.warning(f"Post-migrate auto trade task error: {e}")
