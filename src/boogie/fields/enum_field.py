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
            A subclass of :class:`enum.Enum`. You should consider using
            :class:`boogie.types.DescriptionEnum` in order to provide
            human-friendly names for each enumeration value.
    """

    description = _("An enumeration field")

    def __init__(self, enum, *args, **kwargs):
        if not (isinstance(enum, type) and issubclass(enum, Enum)):
            raise ImproperlyConfigured("First argument must be a enum.Enum subclass.")
        if not list(enum):
            raise ImproperlyConfigured(
                f"Must be a concrete enumeration. The provided class "
                f"{enum.__qualname__} is empty."
            )
        if "choices" in kwargs:
            raise ImproperlyConfigured("Cannot set the choices of an enum field.")
        if not is_integer_enum(enum):
            if "max_length" not in kwargs:
                kwargs["max_length"] = enum_max_length(enum)
            elif kwargs["max_length"] < enum_max_length(enum):
                raise ImproperlyConfigured(
                    "Maximum length is smaller then the larger enum field "
                    "representation."
                )

        self.enum = enum
        if is_integer_enum(enum):
            self._impl = models.SmallIntegerField
        else:
            self._impl = models.CharField
        super().__init__(*args, **kwargs)
        self.choices = get_choices_from_enum(enum)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        args = [self.enum] + args
        kwargs.pop("choices")
        return name, path, args, kwargs

    def get_internal_type(self):
        return self._impl.get_internal_type(self)

    def to_python(self, value):
        if value in self.empty_values:
            return None
        value = self._impl.to_python(self, value)
        return value_to_enum(self.enum, value)

    def get_db_prep_value(self, value, connection, prepared=False):
        value = getattr(value, "value", value)
        prep_value = self._impl.get_db_prep_value
        return prep_value(self, value, connection, prepared=prepared)

    def contribute_to_class(self, cls, name, *args, **kwargs):
        super().contribute_to_class(cls, name, *args, **kwargs)

        # Add options
        prefix = name.upper() + "_"
        for option in self.enum:
            setattr(cls, prefix + option.name, option)

        # Create descriptor that wraps field access. The descriptor guarantees
        # that the object is always converted to Enum types
        setattr(cls, name, EnumDescriptor(self.enum, name))

    def formfield(self, **kwargs):
        # FIXME: Super ugly hack! Try to find a more official solution instead
        # of patching a method of a live instance.
        result = super().formfield(**kwargs)
        result.widget.render = fix_renderer(result.widget.render)
        return result


class EnumDescriptor:
    def __init__(self, enum, name):
        self.enum = enum
        self.name = name

    def __get__(self, instance, cls=None):
        if instance is None:
            return self

        value = instance.__dict__.get(self.name)
        enum = self.enum
        if isinstance(value, (enum, NoneType)):
            return value
        value = value_to_enum(enum, value)
        instance.__dict__[self.name] = value
        return value

    def __set__(self, instance, value):
        enum = self.enum
        if value == "":
            value = next(iter(enum))
        if not isinstance(value, (enum, NoneType)):
            value = value_to_enum(enum, value)
        instance.__dict__[self.name] = value


def fix_renderer(renderer):
    """
    Patch the .render() function of a select widget to use the .value of a enum
    field instead of a Enum instance.
    """

    def render(value=None, **kwargs):
        value = getattr(value, "value", value)
        return renderer(value=value, **kwargs)

    return render


def get_choices_from_enum(enum):
    """
    Return a list of (name, verbose name) choices from an Enum type.
    """

    def human(x):
        return x.lower().replace("_", " ")

    def description(x):
        try:
            return x.description
        except AttributeError:
            return human(x.name)

    if is_integer_enum(enum):
        return tuple((e.value, description(e)) for e in enum)
    else:
        return tuple((e.value, human(e.name)) for e in enum)


@lru_cache(2048)  # noqa C901
def value_to_enum(enum_type, value):
    """
    Create Enum instance from a string value. This will scan the list of
    enumerations if string is not found.
    """

    # Special case valid values
    if isinstance(value, (enum_type, NoneType)):
        return value

    # Simple transformation to enum
    try:
        return enum_type(value)
    except ValueError:
        pass

    # Some types do not
    for obj in enum_type:
        if obj.value == value:
            return obj

    # Maybe we provided the enum name
    if isinstance(value, str):
        try:
            new_value = getattr(enum_type, value)
            if isinstance(new_value, enum_type):
                return new_value
        except (AttributeError, TypeError):
            pass

        # Sometimes the string comes in the form of <TypeName>.<Enum Name>
        if value.startswith(enum_type.__name__ + "."):
            attr = value[len(enum_type.__name__) + 1 :]
            if attr and hasattr(enum_type, attr):
                new_value = getattr(enum_type, attr)
                if isinstance(new_value, enum_type):
                    return new_value

    # Check if value can be coerced to string
    try:
        return enum_type(str(value))
    except ValueError:
        pass

    # Give up!
    raise ValueError("not a valid value for enumeration: %r" % value)


@lru_cache(256)
def is_integer_enum(tt):
    if isinstance(tt, IntEnum):
        return True
    else:
        return all(isinstance(opt.value, int) for opt in tt)


def enum_max_length(tt):
    return max(len(str(opt.value)) for opt in tt)
