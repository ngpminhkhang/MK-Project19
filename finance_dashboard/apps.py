from django.apps import AppConfig

class AumTerminalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'finance_dashboard'

    def ready(self):
        import finance_dashboard.signals