import re

RE_NAME = re.compile(r"^\w+$")
FULL_SLICE = slice(None, None, None)
INIT_TEMPLATE = """
def __init__(self, {fields}):
    self._data = [{fields}]
"""


def linear_namespace(name, fields):
    """
    Construct a mutable namedtuple-like type.

    Args:
        name (str):
            The new type name
        fields:
            A sequence of names for each value of the linear namespace.
    """

    fields = tuple(fields)
    prop = make_item_accessor
    class_dict = dict(__init__=make_init(fields), _fields=fields)
    class_dict.update((name, prop(i)) for i, name in enumerate(fields))
    return type(name, (LinearNamespaceBase,), class_dict)


def linear_namespace_from_sequence(cls, data, copy=True):
    """
    Create a new linear space from a sequence

    If a list is given, and copy=False, it will be reused as data.

    >>> Point = linear_namespace('Point', ['x', 'y'])
    >>> linear_namespace_from_sequence(Point, [1, 2])
    """

    data = list(data)
    if len(data) != len(cls._fields):
        n = len(cls._fields)
        raise ValueError("expected a sequence with %s paramenters" % n)

    new = object.__new__(cls)
    new._data = list(data) if copy or type(data) is not list else data
    return new


def make_init(args):
    """
    Make init function for linear namespace from list of args.
    """

    invalid = [name for name in args if not is_valid_python_name(name)]
    if any(invalid):
        raise ValueError("invalid names: %s" % invalid)
    if len(set(args)) != len(args):
        raise ValueError("arguments cannot be repeated")

    names = ", ".join(args)
    ns = {}
    exec(INIT_TEMPLATE.format(fields=names), ns)
    return ns["__init__"]


def make_item_accessor(idx):
    """
    Returns a property that mirrors access to the idx-th value of an object.
    """

    @property
    def attr(self):
        return self[idx]

    @attr.setter
    def attr(self, value):
        self[idx] = value

    return attr


class LinearNamespaceBase:
    """
    Linear namespace are used as the base class for Row() instances
    in Boogie query sets.
    """

    __slots__ = ("_data",)

    fromseq = classmethod(linear_namespace_from_sequence)

    def __setitem__(self, i, value):
        if i == FULL_SLICE and len(value) != len(self):
            raise ValueError("cannot")
        else:
            self._data[i] = value

    def __getitem__(self, i):
        return self._data.__getitem__(i)

    def __repr__(self):
        args = ", ".join(repr(x) for x in self)
        return "%s(%s)" % (type(self).__name__, args)

    # Sequence
    __iter__ = lambda self: self._data.__iter__()
    __len__ = lambda self: self._data.__len__()

    # Arithmetic
    __add__ = lambda self, x: self._data.__add__(as_data(self, x))
    __radd__ = lambda self, x: as_data(self, x).__add__(self._data)
    __mul__ = lambda self, x: self._data.__mul__(as_data(self, x))
    __rmul__ = lambda self, x: self._data.__rmul__(as_data(self, x))

    # Logical operators
    __eq__ = lambda self, x: self._data.__eq__(as_data(self, x))
    __ne__ = lambda self, x: self._data.__ne__(as_data(self, x))
    __lt__ = lambda self, x: self._data.__lt__(as_data(self, x))
    __le__ = lambda self, x: self._data.__le__(as_data(self, x))
    __gt__ = lambda self, x: self._data.__gt__(as_data(self, x))
    __ge__ = lambda self, x: self._data.__ge__(as_data(self, x))

    # Public list methods that do not change the instance size
    count = lambda self, value: self._data.count(value)
    index = lambda self, value, *args: self._data.index(value, *args)
    sort = lambda self, **kwargs: self._data.sort(**kwargs)
    reverse = lambda self: self._data.reverse()


LINEAR_NAMESPACE_API = {"_fields", "fromseq", "index", "count", "sort", "reverse"}
LINEAR_NAMESPACE_CACHE = {}


def linear_namespace_cached(name, attrs):
    """
    A cached version of linear_namespace.

    This function will always return the same type for each unique combination
    of name, attrs.
    """

    attrs = tuple(attrs)
    try:
        return LINEAR_NAMESPACE_CACHE[name, attrs]
    except KeyError:
        new_type = linear_namespace(name, attrs)
        return LINEAR_NAMESPACE_CACHE.setdefault((name, attrs), new_type)


linear_namespace.fromseq = linear_namespace_from_sequence


#
# Utility functions
#
def is_valid_python_name(name):
    if not name or name[0].isdigit() or name.startswith("__"):
        return False
    if name in LINEAR_NAMESPACE_API:
        return False
    return RE_NAME.match(name) is not None


def as_data(self, other):
    """
    Convert other to a compatible data type.
    """
    if isinstance(other, list):
        return other
    elif isinstance(other, type(self)):
        return other._data
    elif isinstance(other, tuple):
        return list(other)
    return other
