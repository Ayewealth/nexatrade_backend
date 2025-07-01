from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError


class TradingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.trading"

    def ready(self):
        try:
            from .tasks import create_or_update_profit_task, create_or_update_market_price_task
            create_or_update_profit_task()
            create_or_update_market_price_task()
        except (OperationalError, ProgrammingError):
            # This means tables aren't ready yet, so skip for now
            pass
