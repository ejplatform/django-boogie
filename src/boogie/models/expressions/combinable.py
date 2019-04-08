from functools import lru_cache

from django.db.models import BooleanField
from django.db.models.expressions import Combinable


def _method(op):
    return lambda self, other: self._boolean_combine(other, op)


class Comparable(Combinable):
    """
    Mixin class that adds comparison operators (==, != , >, <, >=, <=) to the
    ``Combinable`` interface.
    """

    # Comparison connectors
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    EQ = "="
    NEQ = "<>"

    __gt__ = _method(GT)
    __lt__ = _method(LT)
    __ge__ = _method(GTE)
    __le__ = _method(LTE)
    __eq__ = _method(EQ)
    __ne__ = _method(NEQ)

    def _boolean_combine(self, other, op):
        expression = self._combine(other, op, False)
        expression.output_field = BooleanField()
        expression.comparable_expression = True
        return expression

    def equal(self, other):
        return super().__eq__(other)

    def not_equal(self, other):
        return super().__ne__(other)


def as_comparable(obj):
    """
    Return object as an instance of Comparable class.
    """
    cls = get_comparable_class(type(obj))
    obj.__class__ = cls
    return obj


@lru_cache(maxsize=256)
def get_comparable_class(cls, doc=None):
    if issubclass(cls, Comparable):
        return cls
    ns = {"__doc__": doc} if doc else {}
    return type(cls.__name__ + "Comparable", (Comparable, cls), ns)
