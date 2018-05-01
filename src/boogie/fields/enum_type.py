import enum


class ConditionalDescriptor:
    """
    A descriptor that allows class and instance dispatch to different methods.

    It receives a string name and dispatches to _<name> when accessed from
    an instance and _cls_<name> when accessed from a class.
    """

    def __init__(self, attr):
        self.attr = attr

    def __get__(self, instance, cls=None):
        if instance is None:
            return getattr(cls, '_cls_' + self.attr)
        else:
            return getattr(instance, '_' + self.attr)


class Namespace(enum._EnumDict):
    """
    Namespace that automatically create value() instances for member entries.
    """

    def __init__(self, data):
        super().__init__()
        self.update(data)
        self._last_values.extend(getattr(data, '_last_values', ()))
        self._member_names.extend(getattr(data, '_member_names', ()))
        self._auto_index = 0
        self._enum_values = {}

    def __setitem__(self, key, value):
        if key.isupper():
            if isinstance(value, str):
                value = TaggedInt(self._auto_index, value)
                self._auto_index += 1
            elif isinstance(value, tuple):
                value = TaggedInt(*value)
            elif isinstance(value, TaggedInt):
                self._auto_index = value + 1
            elif isinstance(value, int):
                value = TaggedInt(value, key.lower().replace('_', ' '))
                self._auto_index = value + 1
            # Proxy strings
            elif value == str(value):
                value = TaggedInt(self._auto_index, str(value))
                self._auto_index += 1
            else:
                type_name = value.__class__.__name__
                raise TypeError('unsupported enum value type: %s' % type_name)

            self._enum_values[key] = value

        super().__setitem__(key, value)

    def __getattr__(self, item):
        return getattr(self.data, item)


class DescriptionEnumMeta(enum.EnumMeta):
    """
    Metaclass for DescriptionMenu.
    """

    @classmethod
    def __prepare__(meta, cls, bases):  # noqa: N804
        namespace = super().__prepare__(cls, bases)
        return Namespace(namespace)

    def __init__(cls, name, bases, namespace):  # noqa: N805
        super().__init__(name, bases, namespace)

        # Handle enum values and store metadata
        enum_values = namespace._enum_values
        cls._descriptions = \
            {k: v.description for k, v in enum_values.items()}
        cls._descriptions.update(
            {i: i.description for i in enum_values.values()}
        )

        for k, v in enum_values.items():
            setattr(cls, k + '_DESCRIPTION', v.description)

    def _cls_get_description(cls, value):  # noqa: N805
        """
        Get description from value.
        """
        try:
            return cls._descriptions[value]
        except KeyError:
            raise ValueError('not a member of enumeration: %r' % value)


class IntEnum(enum.IntEnum, metaclass=DescriptionEnumMeta):
    """
    A subclass of enum.IntEnum that accepts an optional human-friendly
    description field during declaration.

    It is safe to translate description strings.

    Usage:
        >>> class Roles(IntEnum):
        ...     TEACHER = 0, 'teacher'
        ...     STUDENT = 1, 'student'

    """

    get_description = ConditionalDescriptor('get_description')

    def _get_description(self):
        """
        Return description string for value member.
        """
        return self.__class__._descriptions[int(self)]


class Enum(enum.Enum, metaclass=DescriptionEnumMeta):
    """
    Similar to :cls:`boogie.IntEnum`, but accepts any type of value.
    """

    get_description = ConditionalDescriptor('get_description')

    def _get_description(self):
        """
        Return description string for value member.
        """
        return self.__class__._descriptions[int(self)]


class TaggedInt(int):
    """
    A tagged integer.
    """

    def __new__(cls, value=0, description=''):
        self = super().__new__(cls, value)
        self.description = description
        return self

    def __repr__(self):
        name = self.__class__.__name__
        return '%s(%s, %r)' % (name, super().__repr__(), self.description)

    __str__ = __repr__
