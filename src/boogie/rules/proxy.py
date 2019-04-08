from collections.abc import Sequence, Mapping
from functools import wraps

from django.db.models import QuerySet
from rules import test_rule
from rules.predicates import NO_VALUE

import sidekick as sk
from sidekick import lazy
from .valuemap import compute


def proxy(obj, user=NO_VALUE, *, values=None, perms=None, rules=None, **kwargs):
    """
    Creates a proxy that augments the given object with all attributes passed
    as keyword arguments. Functions are bound to the obj instance as the
    first argument.
    """
    return Proxy(obj, user, values, perms, rules, kwargs)


def proxy_seq(seq, user=None, *, values=None, perms=None, rules=None, **kwargs):
    """
    Similar to proxy, but expect a sequence/queryset/mapping of objects. It
    augment the items in the collection rather than the collection object
    itself.
    """
    args = (user, values, perms, rules, kwargs)
    if isinstance(seq, QuerySet):
        return QuerySetProxy(seq, *args)
    elif isinstance(seq, Mapping):
        return MappingProxy(seq, *args)
    return CollectionProxy(seq, *args)


#
# Auxiliary classes
#
class Proxy(sk.Proxy):
    """
    Acts as a proxy of objects with arbitrary additional parameters.
    """

    def __init__(self, obj, user, values, perms, rules, kwargs):
        super().__init__(obj)
        self._kwargs = kwargs
        self._user = user
        self._values = values or ()
        self._perms = perms or {}
        self._rules = rules or {}

    def __getattr__(self, attr):
        value = NO_VALUE
        user = self._user
        obj = self._obj__

        if attr in self._kwargs:
            value = self._kwargs[attr]
            if callable(value):
                value = value(self)
        if attr in self._values:
            value_id = self._values[attr]
            value = compute(value_id, obj, user)
        if attr in self._perms and self._user is not NO_VALUE:
            perm = self._perms[attr]
            value = user.has_perm(perm, obj)
        if attr in self._rules:
            rule = self._rules[attr]
            value = test_rule(rule, obj, user)

        if value is NO_VALUE:
            return super().__getattr__(attr)

        setattr(self, attr, value)
        return value


class CollectionProxy(Sequence):
    """
    Acts as a proxy for a immutable collection of objects: i.e., attributes
    are augmented after iteration.
    """

    _args = lazy(lambda x: (x._user, x._values, x._perms, x._rules, x._kwargs))

    def __init__(self, obj, user, values, perms, rules, kwargs):
        self._obj = obj
        self._user = user
        self._values = values
        self._perms = perms
        self._rules = rules
        self._kwargs = kwargs

    def __len__(self):
        return len(self._obj)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return CollectionProxy(self._obj[idx], *self._args)
        return Proxy(self._obj[idx], *self._args)

    def __iter__(self):
        args = self._args
        for obj in self._obj:
            yield Proxy(obj, *args)

    def __bool__(self):
        return bool(self._obj)


class MappingProxy(Mapping, CollectionProxy):
    def __iter__(self):
        return iter(self._obj)

    def items(self):
        args = self._args
        return ((k, Proxy(v, *args)) for k, v in self._obj.items())


class QuerySetProxy(CollectionProxy):
    """
    Acts as a proxy of objects with arbitrary additional parameters.
    """

    def __getattr__(self, attr):
        value = getattr(self._obj, attr)

        if callable(value):
            function = value

            @wraps(function)
            def value(*args, **kwargs):
                result = function(*args, **kwargs)
                if isinstance(result, QuerySet):
                    return QuerySetProxy(result, *self._args)
                return Proxy(result, *self._args)

        setattr(self, attr, value)
        return value
