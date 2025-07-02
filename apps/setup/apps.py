from django.apps import AppConfig
from django.db.models.signals import post_migrate
import logging
import os


class SetupConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.setup"

    def ready(self):
        post_migrate.connect(run_initialize_data, sender=self)


def run_initialize_data(sender, **kwargs):
    if os.environ.get("RUN_INITIALIZE_DATA", "false").lower() == "true":
        from django.core.management import call_command
        try:
            call_command('initialize_data')
        except Exception as e:
            logging.error(f"Error running initialize_data: {e}")
