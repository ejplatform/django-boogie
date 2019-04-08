import inspect
import itertools
import logging
import os
import sys
from importlib import import_module

from django.core.exceptions import ImproperlyConfigured

from .descriptors import Env

log = logging.getLogger("boogie")
NOT_GIVEN = object()


def save_configuration(conf_class, where=None):
    """
    Prepare Django to receive the current configurations. This function is
    usually called at the end of the configuration module and it creates an
    instance of the configuration class and injects all names in its namespace.

    Usage::

        from boogie.configurations import set_configuration, Default

        class Conf(Default):
            MY_OPTION = 42

        init_configuration(Conf)


    Args:
        conf_class:
            A configuration class.
        where:
            The module that it should inject configuration parameters. It can be
            a dictionary or a string with the module path.
    """
    if where is None:
        try:
            where = os.environ["DJANGO_SETTINGS_MODULE"]
        except KeyError:
            raise ImproperlyConfigured(
                "You must either define the DJANGO_SETTINGS_MODULE environment "
                "variable or pass an explicit module name to the "
                "init_configuration function."
            )
    if isinstance(where, str):
        where = import_module(where).__dict__
    elif isinstance(where, type(sys)):
        where = where.__dict__

    # We create an instance of the class configuration and import all symbols
    # with upper case names.
    try:
        conf = conf_class()
        where.update(conf.load_settings())
    except Exception as exc:
        log.error("Error loading configurations: %s" % exc)
        raise


class Conf:
    """
    Base class for all configuration classes.
    """

    ENVFILE = None
    env_prefix = ""

    @classmethod
    def save_settings(cls, where=None):
        """
        Calls :func:`save_configuration` with the current class.
        """
        save_configuration(cls, where)

    def __init__(self, **kwargs):
        self._settings = None
        self.env = Env()

        cls = type(self)
        for name, value in kwargs.items():
            attr = name.upper()
            if hasattr(cls, attr) or hasattr(cls, f"get_{name}"):
                setattr(self, attr, value)
            else:
                raise TypeError(f"invalid argument: {attr}")

    def prepare(self):
        """
        A hook that is executed once after initialization and before creating
        the default settings dictionary.

        The default implementation tries to read an env file if it is defined
        by the ENVFILE settings variable.
        """
        if self.ENVFILE:
            self.env.read_env(self.ENVFILE)

    def finalize(self, settings):
        """
        A hook that receives a settings dictionary and returns the final
        output of the get_settings() method.

        The default implementation simply pass the input dictionary forward.
        """
        return settings

    def load_settings(self):
        """
        Return a dictionary with all settings defined by the configuration.

        This method is idempotent. It caches the resulting settings and always
        return the same settings dictionary.
        """
        if self._settings is None:
            self.prepare()

            # Load standard settings
            settings = {
                attr: getattr(self, attr)
                for attr in set(with_getter_attributes(dir(self)))
            }
            settings = {k: v for k, v in settings.items() if v is not NOT_GIVEN}
            if settings.get("ENVFILE") is None:
                settings.pop("ENVFILE", None)
            self._settings = self.finalize(settings)
        return dict(self._settings)

    def __getattr__(self, attr):
        if attr.isupper():
            func = getattr(self, f"get_{attr.lower()}", None)
            if func is None:
                raise AttributeError(f"Invalid attribute {attr}")
            value = get_value(func, self, attr)
            setattr(self, attr, value)
            return value
        raise AttributeError(attr)


#
# Auxiliary methods
#
def get_value(func, ns, which):
    """
    Evaluate function using given namespace to inject arguments.
    """
    spec = inspect.getfullargspec(func)
    callargs = {}

    with_default = itertools.chain(
        args_with_default(spec.args, spec.defaults or (), NOT_GIVEN),
        [(k, spec.kwonlydefaults[k]) for k in spec.kwonlyargs],
    )
    for name, default in with_default:
        # Skip self
        if name == "self":
            continue

        # The "env" parameter injects the environment variable associated with
        # the attribute
        if name == "env":
            prefix = ns.env_prefix
            attr = which.upper()
            var_name = getattr(func, "env_name", f"{prefix}{attr}")
            type = getattr(func, "env_type", str)
            default = getattr(func, "env_default", default)
            value = ns.env(var_name, type=type, default=default)
            if value is NOT_GIVEN:
                name = which

        # Otherwise we just fetch the variable from the given namespace
        else:
            value = getattr(ns, name.upper(), default)

        # Save variables in dictionary
        if value is NOT_GIVEN:
            var_name = name.upper()
            msg = f"{which}: configuration must define a {var_name} attribute"
            raise TypeError(msg)
        callargs[name] = value

    return func(**callargs)


def args_with_default(names, defaults, fillvalue=None):
    """
    Iterate over pairs of (argument, default) values.
    """
    rnames = reversed(names)
    rdefaults = reversed(defaults)
    pairs = itertools.zip_longest(rnames, rdefaults, fillvalue=fillvalue)
    return reversed(list(pairs))


def with_getter_attributes(attrs):
    for attr in attrs:
        if attr.isupper() and not attr.startswith("_"):
            yield attr
        elif attr.startswith("get_"):
            attr = attr[4:].upper()
            yield attr
