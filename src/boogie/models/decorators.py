from functools import wraps

from .manager import QueryManager


def manager_method(method):
    """
    Decorator that marks a method as a manager method, i.e., it can only be
    accessed by a manager created with QuerySet.as_manager() and not by
    instances of the queryset itself.
    """

    @wraps(method)
    def decorated(self, *args, **kwargs):
        raise TypeError('this method cannot be used from a queryset.')

    decorated._is_manger_method = True
    decorated._original_method = method

    return decorated


def manager_property(method=None, *, classproperty=False):
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

                @manager_property
                def active_authors(self):
                    return self.authors.filter(active=True)


        The ``active_authors`` property is a manager, not a queryset. While most
        manager methods are available to query sets, making them interchangeable
        in many situations, exposing the property as actual managers
        improves the API consistency so users don't have to memorize which
        methods are present in requires calls to .all() and which ones do not.

        >>> [author.name for author in book.active_authors.all()]
        ['Douglas Adams', ...]
    """

    if method is None:
        return lambda f: manager_property(f, classproperty=classproperty)

    class ManagerProperty(property):
        def __get__(self, instance, cls=None):
            if instance is not None:
                return super().__get__(instance, cls)
            elif not classproperty:
                return self
            else:
                return self.fget(cls)

    return ManagerProperty(lambda self: QueryManager(method(self)))
