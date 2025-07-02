from django.apps import AppConfig
from django.db.models.signals import post_migrate
import logging


class TradingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.trading"

    def ready(self):
        post_migrate.connect(run_trading_tasks, sender=self)


def run_trading_tasks(sender, **kwargs):
    try:
        from .tasks import (
            create_or_update_profit_task,
            create_or_update_market_price_task
        )
        create_or_update_profit_task()
        create_or_update_market_price_task()
    except Exception as e:
        logging.warning(f"Post-migrate trading task error: {e}")
