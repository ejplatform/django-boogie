from django.core.exceptions import ImproperlyConfigured

try:
    import rest_framework as _rest
except ImportError:
    raise ImproperlyConfigured(
        'boogie.rest requires Django Rest Framework and some additional '
        'packages to be installed. Please install it using pip install '
        'django-boogie[rest].'
    )

from .base import RestAPI

rest_api = RestAPI()
