from functools import wraps

from django.db.models import Manager
from sidekick import lazy, placeholder as this


def manager_only(method=None):
    """
    Decorator that marks a method as a manager method, i.e., it can only be
    accessed by a manager created with QuerySet.as_manager() and not by
    instances of the queryset itself.

    Usage:

        .. code-block:: python

            # managers.py

            class BookQuerySet(models.QuerySet):
                @manager_only()
                def new_edition(self, book, edition):
                    new = copy(book)
                    new.edition = edition
                    new.save()
                    return new

            BookManager = Manager.from_queryset(BookQuerySet)
    """

    if method is None:
        return manager_only

    name = method.__name__
    msg = "this method cannot be used from a queryset."
    if name != "<lambda>":
        msg = "{name} method cannot be used from a queryset."

    @wraps(method)
    def decorated(self, *args, **kwargs):
        if isinstance(self, Manager):
            return method(self, *args, **kwargs)
        else:
            raise TypeError(msg.format(name=name))

    return decorated


def manager_property(method=None):
    """
    Decorates a method that returns a QuerySet instance and expose it as a
    manager. This is useful to define custom accessors for related value,
    providing a consistent api between your custom managers and the related
    managers automatically created by Django.

    Usage:

        .. code-block:: python

            # models.py

            class Book(models.Model):
                authors = models.ManyToManyField('User')
                ...

                @manager_property()
                def active_authors(self):
                    return self.authors.filter(active=True)


        The ``active_authors`` property is a manager, not a queryset. While most
        manager methods are available to query sets, making them interchangeable
        in many situations, exposing the property as actual managers
        improves the API consistency.

        >>> [author.name for author in book.active_authors.all()]
        ['Douglas Adams', ...]
    """

    if method is None:
        return manager_property

    @wraps(method)
    def wrapped(self):
        return RelatedManager(self, method(self))

    return property(wrapped)


#
# Auxiliary classes
#
def alters_data(func):
    func.alters_data = True
    return func


class RelatedManager(Manager):
    manager = lazy(this.queryset)
    model = lazy(this.queryset.model)
    instance_field = lazy(this.queryset.field.name)
    do_not_call_in_templates = True

    def __init__(self, instance, queryset, instance_field=None):
        super().__init__()
        self.instance = instance
        self.queryset = queryset
        if instance_field is not None:
            self.instance_field = instance_field

    def __getattr__(self, item):
        return getattr(self.manager, item)

    def get_queryset(self):
        return self.queryset

    @alters_data
    def add(self, *objs, bulk=True):
        return self.manager.add(*objs, bulk=True)

    @alters_data
    def create(self, **kwargs):
        kwargs.update(self._construct_params())
        return self.manager.create(**kwargs)

    @alters_data
    def get_or_create(self, **kwargs):
        kwargs.update(self._construct_params())
        return self.manager.get_or_create(**kwargs)

    @alters_data
    def update_or_create(self, **kwargs):
        kwargs.update(self._construct_params())
        return self.manager.update_or_create(**kwargs)

    # remove() and clear() are only provided if the ForeignKey can have a
    # value of null.
    @alters_data
    def remove(self, *objs, bulk=True):
        self._check_nullable_relation()
        return self.manager.remove(*objs, bulk=True)

    @alters_data
    def clear(self, *, bulk=True):
        self._check_nullable_relation()
        return self.manager.clear(bulk=True)

    @alters_data
    def set(self, objs, *, bulk=True, clear=False):
        return self.manager.set(objs, bulk=True, clear=False)

    #
    # Auxiliary methods
    #
    def _check_nullable_relation(self):
        ...  # TODO: check if foreign key relation can hold null values.

    def _construct_params(self):
        # TODO: return mapping with additional params that must be set by
        # using the inverse relation when creating new objects.
        return {}
