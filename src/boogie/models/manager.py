from django.db import models
from django.db.models.sql import Query
from sidekick import delegate_to

from .queryset import QuerySet


class Manager(models.Manager):
    """
    Default Boogie manager.
    """

    # Delegates
    update_dataframe = delegate_to('_queryset')
    load_dataframe = delegate_to('_queryset')
    head = delegate_to('head')
    tail = delegate_to('tail')

    def __getitem__(self, item):
        return self.get_queryset().__getitem__(item)

    def __setitem__(self, item, value):
        return self.get_queryset().__setitem__(item, value)

    def get_queryset(self):
        return QuerySet(self.model, Query(self.model), self._db, self._hints)

    _queryset = property(get_queryset)

    def new(self, *args, **kwargs):
        """
        Create a new model instance, without saving it to the database.
        """
        return self.model(*args, **kwargs)

    def save_dataframe(self, *args, **kwargs):
        return self.get_queryset().save_dataframe(*args, **kwargs)


class QueryManager(Manager):
    """
    A manager object constructed from a queryset instance.
    """

    model = delegate_to('queryset')
    name = delegate_to('queryset')
    _db = delegate_to('queryset')
    _hints = delegate_to('queryset')

    def __init__(self, queryset):
        self._queryset = queryset
        self._used_queryset = False

    def __getattr__(self, item):
        return getattr(self._queryset, item)

    def get_queryset(self):
        if self._used_queryset:
            return self._queryset.all()
        else:
            self._used_queryset = True
            return self._queryset
