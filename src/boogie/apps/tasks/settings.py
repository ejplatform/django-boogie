import logging
from django.conf import settings

REGISTERED_FUNCTIONS = {}
USE_CELERY = bool(getattr(settings, 'CELERY_BROKER', None))

log = logging.getLogger('celery')
