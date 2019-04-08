import importlib
import operator as op

from django.core.exceptions import ImproperlyConfigured
from sidekick import lazy


class LazyMethod:
    """
    Lazily import a method from the given class and inject in the current class
    on first use.
    """

    @lazy
    def object(self):
        try:
            mod = importlib.import_module(self.module)
        except ImportError:
            raise ImproperlyConfigured(
                f"failed to import module: {self.module}\n"
                f"Please install this module in your environment."
            )
        return self.attr_getter(mod)

    def __init__(self, path, pip=None):
        self.module, _, self.path = path.partition(":")
        self.pip = pip
        self.attr_getter = op.attrgetter(self.path)

    def __get__(self, obj, cls=None):
        imported = self.object
        try:
            getter = imported.__get__
        except AttributeError:
            return self if obj is None else obj
        else:
            return getter(obj, cls)

    def __set__(self, obj, value):
        obj = self.object
        obj.__set__(obj, value)

    def __set_name__(self, owner, name):
        self.name = name


def with_base(bases, cls):
    """
    Return a copy of bases tuple that contains the given additional class `cls`.
    """

    if cls in bases:
        return bases

    bases = list(bases)
    tail = []
    while bases:
        if issubclass(cls, bases[-1]):
            tail.append(bases.pop())
        else:
            bases.append(cls)
            break

    return (*bases, *reversed(tail))
