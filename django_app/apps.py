from django.apps import AppConfig
import logging
import atexit


class DjangoAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_app'

    def ready(self):
        logger = logging.getLogger('django_app')
        logger.info("Server started successfully")

        def on_shutdown():
            logger.info("Stopping server")

        atexit.register(on_shutdown)
