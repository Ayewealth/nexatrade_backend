from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connections
from django.db.migrations.executor import MigrationExecutor
import os
import logging


class Command(BaseCommand):
    help = "Deploy command: runs pending migrations and optional data initialization."

    def handle(self, *args, **options):
        # Check for unapplied migrations
        self.stdout.write(self.style.NOTICE(
            "🔍 Checking for pending migrations..."))
        connection = connections['default']
        executor = MigrationExecutor(connection)
        targets = executor.loader.graph.leaf_nodes()
        plan = executor.migration_plan(targets)

        if plan:
            self.stdout.write(self.style.NOTICE(
                "🚀 Running pending migrations..."))
            call_command("migrate")
        else:
            self.stdout.write(self.style.SUCCESS("✅ No pending migrations."))

        # Optionally run initialize_data
        if os.environ.get("RUN_INITIALIZE_DATA", "false").lower() == "true":
            try:
                self.stdout.write(self.style.NOTICE(
                    "📦 Running initialize_data..."))
                call_command("initialize_data")
            except Exception as e:
                logging.error(f"❌ Error running initialize_data: {e}")
                self.stderr.write(self.style.ERROR(
                    f"Failed to run initialize_data: {e}"))
