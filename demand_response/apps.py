from django.apps import AppConfig


class DemandResponseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'demand_response'

    def ready(self):
        import demand_response.signals   # ← connects the signal