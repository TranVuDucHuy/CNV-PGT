from django.apps import AppConfig


class SampleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.features.sample'
    verbose_name = 'Sample Management'

