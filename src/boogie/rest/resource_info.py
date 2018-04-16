from copy import copy

from django.db.models import Model, AutoField
from django.utils.functional import cached_property

from .utils import natural_base_url


class ResourceInfo:
    model_name = cached_property(lambda self: self.model.__name__)

    @cached_property
    def field_names(self):
        return [f.name for f in self.model._meta.fields]

    def __init__(self, model: Model,
                 # Fields
                 fields=None, exclude=(),

                 # Urls
                 base_url=None, base_name=None):
        self.model = model
        self.meta = model._meta
        self.model_fields = {f.name: f for f in self.meta.fields}

        # Field info
        self.fields = list(fields or fields_from_model(model))
        for field in exclude:
            self.fields.remove(field)
        self.used_fields = {f for f in self.fields}

        # Url info
        self.base_url = base_url or natural_base_url(model)
        self.base_name = base_name or natural_base_url(model)

        # Hooks
        self.detail_actions = {}
        self.list_actions = {}
        self.properties = {}

    def copy(self):
        """
        Return a copy of itelf.
        """
        return copy(self)

    def add_field(self, name, db_name=None):
        """
        Register a new field name.
        """
        db_name = db_name or name
        self.fields.append(name)

        if name in self.model_fields:
            field = self.model_fields[name]
            self.used_fields_map.append(field)

    def add_property(self, name, method):
        """
        Register a property with the provided name.

        Args:
            name:
                Property name.
            method:
                A function f(obj) -> value that receives a model instance and
                return the corresponding property value.
        """
        self.add_field(name)
        self.properties[name] = method

    def add_action(self, name, method, detail=True):
        """
        Register an action with the given name.
        """
        raise NotImplementedError


def fields_from_model(model):
    return [f.name for f in model._meta.fields if not isinstance(f, AutoField)]
