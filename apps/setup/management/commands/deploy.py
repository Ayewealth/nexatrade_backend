from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connections
from django.db.migrations.executor import MigrationExecutor
import os
import logging


class Command(BaseCommand):
    help = "Deploy command: safely runs makemigrations, migrate, and optional data initialization."

    def handle(self, *args, **options):
        # Step 1: Run makemigrations but do NOT create empty migrations
        self.stdout.write(self.style.NOTICE(
            "🛠️ Checking for model changes and making migrations..."))
        try:
            # --check detects if any migration files need to be created, returns non-zero if none needed
            # So we use makemigrations normally but check for empty migrations afterwards
            call_command("makemigrations", interactive=False)

            # Optional: you can add a check for empty migrations and warn if any created
            # (Django doesn't create migrations if nothing changed)
        except Exception as e:
            logging.error(f"❌ Error running makemigrations: {e}")
            self.stderr.write(self.style.ERROR(
                f"Failed to run makemigrations: {e}"))
            # Fail here because makemigrations failed (optional)
            return

        # Step 2: Check for unapplied migrations
        self.stdout.write(self.style.NOTICE(
            "🔍 Checking for pending migrations..."))
        connection = connections['default']
        executor = MigrationExecutor(connection)
        targets = executor.loader.graph.leaf_nodes()
        plan = executor.migration_plan(targets)

        if plan:
            self.stdout.write(self.style.NOTICE(
                "🚀 Running pending migrations..."))
            try:
                call_command("migrate", interactive=False)
            except Exception as e:
                logging.error(f"❌ Error running migrate: {e}")
                self.stderr.write(self.style.ERROR(
                    f"Failed to run migrate: {e}"))
                return
        else:
            self.stdout.write(self.style.SUCCESS("✅ No pending migrations."))

        # Step 3: Optionally run initialize_data
        if os.environ.get("RUN_INITIALIZE_DATA", "false").lower() == "true":
            try:
                self.stdout.write(self.style.NOTICE(
                    "📦 Running initialize_data..."))
                call_command("initialize_data")
            except Exception as e:
                logging.error(f"❌ Error running initialize_data: {e}")
                self.stderr.write(self.style.ERROR(
                    f"Failed to run initialize_data: {e}"))
