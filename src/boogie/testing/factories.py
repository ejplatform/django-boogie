import inspect

import factory as _factory
from factory import DjangoModelFactory, Factory
from factory import declarations
from factory.declarations import BaseDeclaration
from faker import Factory as FakeFactory
from model_mommy.mommy import Mommy

fake = FakeFactory.create()

FactoryMeta = type(DjangoModelFactory)


def __getitem__(self, idx):
    if isinstance(idx, slice):
        pass
    return ...


FactoryMeta.__getitem__ = __getitem__


class BoogieMommy(Mommy):
    """
    Base for Boogie Model Mommy classes.
    """

    attr_mapping = {}
    type_mapping = {}


#
# Declarations
#
class ImplicitDeclaration(BaseDeclaration):
    def __init__(self):
        pass


#
# Factory function
#
def factory(model, **kwargs):
    """
    Creates a factory boy factory class
    """

    ns = {"Meta": type("Meta", (), {"model": model})}

    # Handle explicitly declared values
    for k, v in kwargs:
        ns[k] = explicit_declaration(model, k, v)

    # Create mommy instance to help with automatic value generation
    mommy = Mommy(model)

    # Create implicit declarations
    for field in model._meta.fields:
        if not requires_declaration(model, field.name, ns):
            continue
        ns[field.name] = implicit_declaration(model, field.name, ns, mommy)

    return type(model.__name__ + "Factory", (DjangoModelFactory,), ns)


def explicit_declaration(model, name, value):
    """
    Return a Declaration instance that implements an explicitly defined field
    for a model.

    Args:
        model:
            Model class
        name:
            Name of the field in the model
        value:
            Value explicitly passed by the user
    """
    if issubclass(value, BaseDeclaration):
        return value
    elif isinstance(value, type) and issubclass(value, Factory):
        return _factory.SubFactory(value)
    elif callable(value):
        if has_no_args(value):
            return _factory.LazyFunction(value)
        else:
            return _factory.LazyAttribute(value)
    elif isinstance(value, str):
        return _factory.LazyAttribute(lambda x: value.format(model=x))
    else:
        return value


def requires_declaration(model, name, definitions):
    """
    Return True if explicit generation of given field is required during model
    instantiation.

    Args:
        model:
            Model class
        name:
            Model field name
        definitions:
            A map of names of all explicitly defined fields to their
            corresponding defined values.
    """
    field = model._meta.get_field(name)
    if field.has_default() or field.auto_created:
        return False
    if field in definitions:
        return False
    return True


def implicit_declaration(model, name, definitions, mommy):
    """
    Creates an implicit declaration for the field.

    Receives the same arguments as :func:`requires_declaration`, but returns
    a declaration instance.
    """

    field = model._meta.get_field(name)
    try:
        faker = getattr(fake, name)
        return declarations.LazyFunction(faker)
    except AttributeError:
        generator = lambda: mommy.generate_value(field, commit=False)
        return declarations.LazyFunction(generator)


def has_no_args(func):
    """
    Return True if function is called with no positional args.
    """
    try:
        spec = inspect.getfullargspec(func)
    except TypeError:
        return has_no_args(func.__call__)
    return bool(spec.args)
