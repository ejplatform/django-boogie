import enum


class _EnumDict(enum._EnumDict):
    """
    Namespace that automatically create value() instances for member entries.
    """

    def __init__(self, dtype=object):
        super().__init__()
        self.dtype = dtype
        self._descriptions = []

    def __setitem__(self, key, value):
        if key == 'description':
            raise ValueError('invalid enum name')
        super().__setitem__(key, value)

        if self._member_names and self._member_names[-1] == key:
            if not isinstance(value, tuple):
                if isinstance(value, self.dtype):
                    value = (value, key)
                elif isinstance(value, str):
                    value = (None, value)
                else:
                    value = (value, key)

            value, description = value
            self._last_values[-1] = value
            self._descriptions.append(description)
            dict.__setitem__(self, key, value)


class EnumMeta(enum.EnumMeta):
    dtype = object

    @classmethod
    def __prepare__(meta, cls, bases):  # noqa: N804
        enum_dict = _EnumDict(meta.dtype)
        member_type, first_enum = meta._get_mixins_(bases)
        if first_enum is not None:
            enum_dict['_generate_next_value_'] = getattr(first_enum, '_generate_next_value_', None)
        return enum_dict

    def __new__(meta, name, bases, namespace):  # noqa: N804
        values = namespace._last_values
        names = namespace._member_names

        # Update
        if meta.dtype is int:
            for idx, (key, value) in enumerate(zip(names, values)):
                values[idx] = value = idx if value is None else value
                dict.__setitem__(namespace, key, value)
            namespace._last_values = values

        new = super().__new__(meta, name, bases, namespace)
        return new

    def __init__(cls, name, bases, namespace):  # noqa: N805
        super().__init__(name, bases, namespace)

        # Save descriptions
        names = namespace._member_names
        descriptions = namespace._descriptions
        values = namespace._last_values

        cls._descriptions = dict(zip(names, descriptions))
        cls._values = dict(zip(names, values))
        for attr, descr in zip(names, descriptions):
            setattr(cls, attr + '_DESCRIPTION', descr)
            case = getattr(cls, attr)
            case.description = str(descr)
            cls._descriptions[case] = str(descr)

    def __hash__(cls):  # noqa: N805
        return id(cls)

    def get_description(cls, value):  # noqa: N805
        """
        Get description from value.
        """
        try:
            return cls._descriptions[value]
        except KeyError:
            raise ValueError('not a member of enumeration: %r' % value)


class IntEnum(enum.IntEnum,
              metaclass=type('IntEnumMeta', (EnumMeta,), {'dtype': int})):
    """
    A subclass of enum.IntEnum that accepts an optional human-friendly
    description field during declaration.

    It is safe to translate description strings.

    Usage:
        >>> class Roles(IntEnum):
        ...     TEACHER = 0, 'teacher'
        ...     STUDENT = 1, 'student'
    """


class Enum(enum.Enum, metaclass=EnumMeta):
    """
    Similar to :cls:`boogie.IntEnum`, but accepts any type of value.
    """

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return other is self
        else:
            return self.value.__eq__(other)
