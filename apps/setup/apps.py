from django.apps import AppConfig
from django.db.models.signals import post_migrate
import logging
import os
import sys

BUILDING = 'collectstatic' in sys.argv or 'migrate' in sys.argv


class SetupConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.setup"

    def ready(self):
        if not BUILDING:
            post_migrate.connect(run_initialize_data, sender=self)


def run_initialize_data(sender, **kwargs):
    if os.environ.get("RUN_INITIALIZE_DATA", "false").lower() == "true":
        from django.core.management import call_command
        try:
            print("Running initialize_data after migrations...")
            call_command('initialize_data')
        except Exception as e:
            logging.error(f"Error running initialize_data: {e}")
