from django.apps import AppConfig

class SalesApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        from .signals import setup_roles
        setup_roles()