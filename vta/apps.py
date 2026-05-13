"""App configuration for VTA."""

from django.apps import AppConfig


class VtaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vta'
    verbose_name = 'Value Tree Analysis'