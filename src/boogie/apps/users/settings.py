from django.conf import settings

REGISTERED_FUNCTIONS = {}

MIN_USERS = getattr(settings, 'EJ_MATH_MIN_USERS', 5)
MIN_COMMENTS = getattr(settings, 'EJ_MATH_MIN_COMMENTS', 5)
MIN_VOTES = getattr(settings, 'EJ_MATH_MIN_VOTES', 5)
USE_CELERY = bool(getattr(settings, 'CELERY_BROKER', None))
