from django.apps import apps as _apps

# Import all fields and models. boogie.models serves as a drop-in replacement
# for django models.
from django.db.models import *
from model_utils.models import TimeStampedModel, TimeFramedModel, StatusModel, \
    SoftDeletableModel, SoftDeletableManager, StatusField, AutoCreatedField, \
    MonitorField, AutoLastModifiedField, QueryManager

# Check dependencies before loading custom modules
from .abstract import User, Profile

# Overload Django objects
from .manager import Manager
from .queryset import QuerySet
from .expressions import F, concat, coalesce, greatest, least

# Load Boogie features
from .decorators import manager_method
from ..fields import *

# Django manager utils standalone functions. This is useful for people not using
# boogie managers, but still wants to perform bulk operations
from manager_utils import bulk_update, bulk_upsert, post_bulk_operation, \
    single, upsert, get_or_none, id_dict, sync

# Django pandas functions
from django_pandas.io import read_frame
