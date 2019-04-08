from django.core.exceptions import ImproperlyConfigured

try:
    import rest_framework as _rest
except ImportError:
    raise ImproperlyConfigured(
        "boogie.rest requires Django Rest Framework and some additional "
        "packages to be installed. Please install it using pip install "
        "django-boogie[rest]."
    )

from .rest_api import RestAPI
from .utils import to_json_default
from . import utils as _utils

rest_api = RestAPI()
_utils.patch_rest_framework_json_encoder()
