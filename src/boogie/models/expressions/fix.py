from django.db import models
from django.db.models import Field, Lookup, Q
from django.db.models.sql import Query


#
# In order to support the __ne query, we monkey patch Django's Query class to
# accept the __ne suffix. This will make expressions such as "F.value != value"
# work both in boogie and in the vanilla queryset API.
#
@Field.register_lookup
class NotEqual(Lookup):
    lookup_name = "ne"

    def as_sql(self, *args):
        lhs, lhs_params = self.process_lhs(*args)
        rhs, rhs_params = self.process_rhs(*args)
        return "%s <> %s" % (lhs, rhs), lhs_params + rhs_params


def patch_query(query_class=Query):
    """
    Patches Query class to accept 'ne' lookups
    """
    # Build lookup
    build_lookup_original = query_class.build_lookup

    def build_lookup(self, lookups, lhs, rhs):
        if rhs is None and lookups[-1:] == ["ne"]:
            rhs, lookups[-1] = False, "isnull"
        return build_lookup_original(self, lookups, lhs, rhs)

    query_class.build_lookup = build_lookup

    # Resolve lookup
    if hasattr(query_class, "resolve_lookup_value"):
        return patch_query_with_resolve_lookup_value(query_class)


def patch_query_with_resolve_lookup_value(query_class=Query):
    resolve_lookup_value_original = query_class.resolve_lookup_value

    def resolve_lookup_value(self, value, lookups, *args):
        if value is None and lookups[-1:] == ["ne"]:
            value, lookups[-1] = False, "isnull"
        return resolve_lookup_value_original(self, value, lookups, *args)

    query_class.prepare_lookup_value = resolve_lookup_value


#
# Utility methods
#
def lookup_method(lookup):
    """Factory function for lookup methods."""

    def method(self, value):
        key = "%s__%s" % (self._name, lookup)
        return Q(**{key: value})

    method.__doc__ = "Performs an name__%s lookup" % lookup
    method.__name__ = lookup
    return method


def lookup_property(lookup):
    """Factory function for simple lookup properties."""

    def fget(self):
        return type(self)("%s__%s" % (self._name, lookup))

    return property(fget)


def delegate_to_f_object(attr):
    def delegate(self, *args, **kwargs):
        obj = models.F(self._name)
        method = getattr(obj, attr)
        return method(*args, **kwargs)

    delegate.__name__ = delegate.__qualname__ = attr
    return delegate


# Execute monkey patch
patch_query()
