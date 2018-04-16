from django.apps import apps as _apps

# Import all fields and models. boogie.models serves as a drop-in replacement
# for django models.
from .decorators import manager_method
from ..fields import EnumField, IntEnum
from django.db.models import *

# Check dependencies before loading custom modules
from .abstract import User, Profile

# Overload Django objects
from .manager import Manager
from .queryset import QuerySet
from .expressions import F, concat, coalesce, greatest, least
