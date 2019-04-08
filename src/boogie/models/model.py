from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models.base import ModelBase as DjangoModelBase
from sidekick import import_later

from .manager import Manager
from .utils import with_base

model_utils = import_later("model_utils.models")
polymorphic = import_later("polymorphic.models")


class ModelBase(DjangoModelBase):
    """
    Base metaclass for Boogie models.
    """

    def __new__(metacls, name, bases, ns, **kwargs):
        # Extract the correct base class
        bases, kwargs = extract_bases(bases, **kwargs)

        # Is abstract
        if "Meta" in ns:
            is_abstract = getattr(ns["Meta"], "abstract", False)
        else:
            is_abstract = False

        # Add default manager to class
        if not is_abstract and "objects" not in ns:
            ns["objects"] = manager = Manager()
            manager.auto_created = True

        # Additional arguments are passed to the Meta class object
        if kwargs and "Meta" in ns:
            raise ImproperlyConfigured(
                "Cannot pass meta arguments to class constructor and the Meta "
                "class simultaneously."
            )
        if kwargs:
            ns["Meta"] = type("Meta", (), kwargs)

        # Create class using default methods.
        return super().__new__(metacls, name, bases, ns)


#
# Utility
#
def extract_bases(
    bases,
    timestamped=False,
    timeframed=False,
    status=False,
    soft_deletable=False,
    polymorphic=False,
    **kwargs
):
    # Inject custom base classes from metaclass options.
    if timeframed:
        bases = with_base(bases, model_utils.TimeFramedModel)
    if timestamped:
        bases = with_base(bases, model_utils.TimeStampedModel)
    if status:
        bases = with_base(bases, model_utils.StatusModel)
    if soft_deletable:
        bases = with_base(bases, model_utils.SoftDeletableModel)
    if polymorphic:
        bases = with_base(bases, polymorphic.PolymorphicModel)

    return bases, kwargs


#
# Base model
#
class Model(models.Model, metaclass=ModelBase, abstract=True):
    """
    Base class for Boogie model.
    """
