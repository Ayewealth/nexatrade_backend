from django.apps import AppConfig
import os


class SetupConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.setup"

    def ready(self):
        if os.environ.get("RUN_INITIALIZE_DATA", "false") == "true":
            from django.core.management import call_command
            try:
                call_command('initialize_data')
            except Exception as e:
                import logging
                logging.error(f"Error running initialize_data: {e}")
