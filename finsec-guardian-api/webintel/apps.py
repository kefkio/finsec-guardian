"""
WebIntel Django App Configuration
"""

from django.apps import AppConfig


class WebintelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'webintel'
    verbose_name = 'Web Intelligence Module'
    
    def ready(self):
        """App initialization."""
        # Import signals if any
        pass
