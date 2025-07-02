from django.core.management.base import BaseCommand
from django.core.management import call_command
import os
import logging


class Command(BaseCommand):
    help = "Deploy command: runs migrations and optional data initialization."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🚀 Running migrations..."))
        call_command("migrate")

        if os.environ.get("RUN_INITIALIZE_DATA", "false").lower() == "true":
            try:
                self.stdout.write(self.style.NOTICE(
                    "📦 Running initialize_data..."))
                call_command("initialize_data")
            except Exception as e:
                logging.error(f"❌ Error running initialize_data: {e}")
                self.stderr.write(self.style.ERROR(
                    f"Failed to run initialize_data: {e}"))
