from django.conf import settings


def get_config(key, default=None):
    """
    Get settings from django.conf if exists or return default value otherwise.
    """
    return getattr(settings, key, default)
