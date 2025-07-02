from django.apps import AppConfig


class SetupConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.setup"

    def ready(self):
        # No need to run anything here anymore
        # The `deploy` command handles initialization after migration
        pass
