from django.apps import AppConfig
import logging
import atexit

logger = logging.getLogger('django_app')

class DjangoAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_app'

    def ready(self):
        logger.info('"Server started successfully"')

        def shutdown_handler():
            logger.info('"Stopping server"')

        atexit.register(shutdown_handler)
