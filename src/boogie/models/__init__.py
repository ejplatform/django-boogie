from django.apps import apps as _apps

# Import all fields and models. boogie.models serves as a drop-in replacement
# for django models.
from django.db.models import *

# Overload Django objects
from .manager import Manager
from .queryset import QuerySet
from .model import Model
from .expressions import F, concat, coalesce, greatest, least

# Load Boogie features
from .methodregistry import manager_method, queryset_method
from ..fields import *
