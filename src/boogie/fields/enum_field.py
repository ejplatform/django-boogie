import enum
from functools import lru_cache

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.translation import ugettext_lazy as _
from sidekick import lazy

NoneType = type(None)


class EnumField(models.Field):
    """
    A Field type that wraps an enumeration.

    It represents each field internally as an integer.

    Args:
        enum_type (type):
            A subclass of :cls:`enum.Enum`. You should consider using
            :cls:`boogie.types.DescriptionEnum` in order to provide
            human-friendly names for each enumeration value.
        is_string (bool):
            If True, data is stored as text in a CharField. The default behavior
            is to store data as integers.
    """

    description = _('An enumeration (using %(is_string)s)')

    @lazy
    def max_abs_value(self):
        return 2 ** 30

    @lazy
    def max_enum_length(self):
        return 10

    def __init__(self, enum_type, *args, is_string=False, **kwargs):
        if not isinstance(enum_type, type) or \
                not issubclass(enum_type, enum.Enum):
            raise ImproperlyConfigured(
                'First argument must be a enum.Enum subclass.'
            )
        if not issubclass(enum_type, enum.IntEnum) and not is_string:
            raise ImproperlyConfigured(
                'Plain enum types are serialized as strings. Either use an '
                'IntEnum enumeration or set is_string=True.'
            )

        self.is_string = is_string
        self.enum_type = enum_type

        # Control maximum length for char fields
        if kwargs.get('max_length', 2 ** 64) < self.max_enum_length:
            raise ImproperlyConfigured(
                'Maximum length is smaller then the larger enum field '
                'representation.'
            )
        if is_string and 'max_length' not in kwargs:
            kwargs['max_length'] = self.max_enum_length

        # Choices
        if 'choices' in kwargs:
            raise ImproperlyConfigured(
                'Cannot set the choices of an enum field.'
            )
        kwargs['choices'] = get_choices_from_enum(enum_type, is_string)

        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        args = [self.enum_type] + args
        del kwargs['choices']
        kwargs['is_string'] = self.is_string
        return name, path, args, kwargs

    def get_internal_type(self):
        if self.is_string:
            return 'CharField'
        elif self.max_abs_value < 32767:
            return 'SmallIntegerField'
        else:
            return 'IntegerField'

    def from_db_value(self, value, expression, connection, context):
        return self.to_python(value)

    def to_python(self, value):
        if isinstance(value, (self.enum_type, NoneType)):
            return value

        if self.is_string or isinstance(value, str):
            return enum_from_str_value(self.enum_type, value)
        else:
            return self.enum_type(int(value))

    def get_db_prep_value(self, *args, **kwargs):
        value = super().get_db_prep_value(*args, **kwargs)

        if value is None:
            return None
        elif self.is_string:
            return str(getattr(value, 'value', value))
        elif isinstance(value, str):
            if value == '':
                return None
            enum = enum_from_str_value(self.enum_type, value)
            return int(enum.value)
        else:
            return int(value)

    def contribute_to_class(self, cls, name, *args, **kwargs):
        super().contribute_to_class(cls, name, *args, **kwargs)
        prefix = name.upper() + '_'
        for option in self.enum_type:
            setattr(cls, prefix + option.name, option)


def get_choices_from_enum(enum_type, is_string=False):
    """
    Return a list of (name, verbose name) choices from an Enum type.
    """

    def human(x):
        return x.lower().replace('_', ' ')

    def description(x):
        try:
            return x.get_description()
        except AttributeError:
            return human(x.name)

    if is_string:
        return tuple((e.value, human(e.name)) for e in enum_type)
    else:
        return tuple((e.value, description(e)) for e in enum_type)


@lru_cache(2048)
def enum_from_str_value(enum_type, value):
    """
    Create Enum instance from a string value. This will scan the list of
    enumerations if string is not found.
    """
    try:
        return enum_type(value)
    except ValueError:
        for enum_value in enum_type:
            if str(enum_value.value) == value:
                return enum_value
        for enum_value in enum_type:
            if enum_value.name == value:
                return enum_value

        raise ValueError('not a valid value for enumeration: %r' % value)
