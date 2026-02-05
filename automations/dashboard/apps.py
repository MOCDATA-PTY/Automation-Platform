from django.apps import AppConfig
import os


class DashboardConfig(AppConfig):
    name = 'dashboard'

    def ready(self):
        # Only start scheduler in the main process (not in reloader)
        if os.environ.get('RUN_MAIN') == 'true':
            from . import scheduler
            scheduler.start_scheduler()
