from enum import Enum, IntEnum
from functools import lru_cache

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.translation import ugettext_lazy as _

NoneType = type(None)


class EnumField(models.Field):
    """
    A Field type that wraps an enumeration.

    It represents each field internally as a string or integer.

    Args:
        enum (type):
            A subclass of :cls:`enum.Enum`. You should consider using
            :cls:`boogie.types.DescriptionEnum` in order to provide
            human-friendly names for each enumeration value.
    """

    description = _('An enumeration field')

    def __init__(self, enum, *args, **kwargs):
        if not (isinstance(enum, type) and issubclass(enum, Enum)):
            raise ImproperlyConfigured(
                'First argument must be a enum.Enum subclass.'
            )
        if 'choices' in kwargs:
            raise ImproperlyConfigured(
                'Cannot set the choices of an enum field.'
            )
        if not is_integer_enum(enum):
            if 'max_length' not in kwargs:
                kwargs['max_length'] = enum_max_length(enum)
            elif kwargs['max_length'] < enum_max_length(enum):
                raise ImproperlyConfigured(
                    'Maximum length is smaller then the larger enum field '
                    'representation.'
                )

        self.enum = enum
        if is_integer_enum(enum):
            self._internal_field_class = models.SmallIntegerField
        else:
            self._internal_field_class = models.CharField
        kwargs['choices'] = get_choices_from_enum(enum)
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        args = [self.enum] + args
        del kwargs['choices']
        return name, path, args, kwargs

    def get_internal_type(self):
        return self._internal_field_class.get_internal_type(self)

    def from_db_value(self, value, expression, connection, context):
        return self.to_python(value)

    def to_python(self, value):
        if not isinstance(value, self.enum):
            value = value_to_enum(self.enum, value)
        value = self._internal_field_class.to_python(self, value)
        return value_to_enum(self.enum, value)

    def get_db_prep_value(self, value, connection, prepared=False):
        value = getattr(value, 'value', value)
        prep_value = self._internal_field_class.get_db_prep_value
        return prep_value(self, value, connection, prepared=prepared)

    def contribute_to_class(self, cls, name, *args, **kwargs):
        super().contribute_to_class(cls, name, *args, **kwargs)
        prefix = name.upper() + '_'
        for option in self.enum:
            setattr(cls, prefix + option.name, option)


def get_choices_from_enum(enum):
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

    if is_integer_enum(enum):
        return tuple((e.value, description(e)) for e in enum)
    else:
        return tuple((e.value, human(e.name)) for e in enum)


@lru_cache(2048)
def value_to_enum(enum_type, value):
    """
    Create Enum instance from a string value. This will scan the list of
    enumerations if string is not found.
    """
    if value is None:
        return None
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


@lru_cache(256)
def is_integer_enum(tt):
    if isinstance(tt, IntEnum):
        return True
    else:
        return all(isinstance(opt.value, int) for opt in tt)


def enum_max_length(tt):
    return max(len(str(opt.value)) for opt in tt)
