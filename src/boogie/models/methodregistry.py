from functools import wraps

from django.db import models

#
# Global constants
#
QUERYSET_METHODS = {}
MANAGER_METHODS = {}


#
# Public decorators and functions
#
def manager_method(model, name=None):
    """
    Decorator that marks function to be injected as a manager method for the
    supplied model.
    """
    return _manager_method(model, name)


def queryset_method(model, skip_manager=False, name=None):
    """
    Decorator that marks function to be injected as a queryset method for the
    supplied model.
    """

    def decorator(func):
        if not skip_manager:
            manager_func = lambda m: func(m.get_queryset())
            manager_method(model, name=name)(wraps(func)(manager_func))
        return _queryset_method(model, name=name)(func)

    return decorator


def get_queryset_attribute(qs, attr):
    """
    Return an attribute registered with the :func:`queryset_method` decorator.
    """
    return get_attribute(qs, attr, QUERYSET_METHODS)


def get_manager_attribute(qs, attr):
    """
    Return an attribute registered with the :func:`manager_method` decorator.
    """
    return get_attribute(qs, attr, MANAGER_METHODS)


#
# Auxiliary functions
#
def get_attribute(qs, attr, registry):
    """
    Common implementation to `func`:get_queryset_attr
    """

    if attr.startswith("_"):
        return NotImplemented

    model = qs.model
    try:
        return registry[(model, attr)](qs)
    except KeyError:
        pass

    # Search MRO
    django_model = models.Model
    for cls in model.mro():
        if issubclass(cls, django_model):
            try:
                method = registry[(cls, attr)]
            except KeyError:
                continue
            registry[(model, attr)] = method
            return get_descriptor(method, qs)
    return NotImplemented


def get_descriptor(descriptor, instance):
    try:
        getter = descriptor.__get__
    except AttributeError:
        return descriptor
    else:
        return getter(instance, type(instance))


def registry_decorator(registry):
    """
    Common implementation to @queryset and @manager decorators.
    """

    def register(model, name=None):
        def decorator(obj):
            attr = name or obj.__name__
            if hasattr(obj, "__get__"):
                getter = obj.__get__
                registry[(model, attr)] = lambda qs: getter(qs, type(qs))
            else:
                registry[(model, attr)] = lambda qs: obj
            return obj

        return decorator

    return register


_queryset_method = registry_decorator(QUERYSET_METHODS)
_manager_method = registry_decorator(MANAGER_METHODS)
