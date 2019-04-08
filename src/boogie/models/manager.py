from django.db import models
from django.db.models.manager import BaseManager
from sidekick import delegate_to

from .methodregistry import get_manager_attribute
from .queryset import QuerySet


class Manager(models.Manager, BaseManager):
    """
    Default Boogie manager.
    """

    # Delegate to queryset
    _queryset_class = QuerySet
    to_pivot_table = delegate_to("_queryset")
    to_timeseries = delegate_to("_queryset")
    to_dataframe = delegate_to("_queryset")
    id_dict = delegate_to("_queryset")
    bulk_upsert = delegate_to("_queryset")
    sync = delegate_to("_queryset")
    upsert = delegate_to("_queryset")
    get_or_none = delegate_to("_queryset")
    single = delegate_to("_queryset")
    bulk_update = delegate_to("_queryset")
    index = delegate_to("_queryset")
    dataframe = delegate_to("_queryset")
    select_columns = delegate_to("_queryset")
    update_item = delegate_to("_queryset")
    update_from_dataframe = delegate_to("_queryset")
    pivot_table = delegate_to("_queryset")
    extend_dataframe = delegate_to("_queryset")
    head = delegate_to("_queryset")
    tail = delegate_to("_queryset")

    def __getitem__(self, item):
        return self.get_queryset().__getitem__(item)

    def __setitem__(self, item, value):
        return self.get_queryset().__setitem__(item, value)

    def __getattr__(self, attr):
        value = get_manager_attribute(self, attr)
        if value is NotImplemented:
            raise AttributeError(attr)
        return value

    def get_queryset(self):
        return self._queryset_class(model=self.model, using=self._db, hints=self._hints)

    _queryset = property(get_queryset)

    def new(self, *args, **kwargs):
        """
        Create a new model instance, without saving it to the database.
        """
        return self.model(*args, **kwargs)
