import functools
from pathlib import Path

import environ

path_type = type(Path("path"))


def env(default, type=None, name=None, **kwargs):
    """
    Declare a value that can be overridden by environment variables.

    Usage:
        Used in class declarations:

        class Conf:
            THE_ANSWER = env(42)

        Now Conf instances have an THE_ANSWER attribute that has a default value
        of 42, but can be overridden by a "THE_ANSWER" environment variable.
        If the configuration class define a ``env_prefix`` attribute, it will be
        prepended to the name of the environment variable.

    Args:
        default:
            The default value for the variable, if not present in the
            environment.
        type:
            Variable type. Usually this can be inferred from the default value.
            Boogie also accept some special values described bellow.
        name:
            Explicit name of the environment variable. By default, the name is
            derived from ``<class>.env_prefix + <attribute_name>``.

    Notes:
        Boogie understands the following builtin types: str, bool, int, float,
        list, dict and tuple. It also understands the following pseudo-types:

        json:
            Environment holds arbitrary JSON data.
        path:
            Path to a valid file in the filesystem. Returns a
            :class:`pathlib.Path` instance.
        db_url:
            URL to a database connection, e.g., sqlite:///db.sqlite3 or
            psql://user:password@domain:port/database
        cache_url:
            URL to cache provider, e.g., memcache://host:port
        search_url:
            URL to search provider, e.g., elasticsearch://host:port
        email_url:
            URL to e-mail provider, e.g., smtp+ssl://host:port

    Returns:
        A env variable descriptor
    """
    return EnvDescriptor(default, type=type, name=name, **kwargs)


def env_settings(**kwargs):
    """
    Configure information about environment variable associated with the given
    method. This controls how the "env" attribute is exposed to the function.

    Args:
        name:
            Name of the environment variable.
        type:
            Type (str, int, float, bool, etc).
    """
    valid_kwargs = {"name", "type", "default"}

    def decorator(func):
        for k, v in kwargs.items():
            if k not in valid_kwargs:
                raise TypeError(f"invalid argument: {k}")
            setattr(func, f"env_{k}", v)
        return func

    return decorator


def env_default(**options):
    """
    Use env variable, if set, otherwise execute function to compute attribute.
    """
    not_given = object()

    def decorator(func):
        name = getattr(func, "env_name", func.__name__)
        type = getattr(func, "env_type", str)
        default = getattr(func, "env_default", not_given)

        @functools.wraps(func)
        def decorated(self):
            value = self.env(name, type=type, default=default)
            if value is not_given:
                return func(self)
            return value

        return decorated

    return decorator


class EnvDescriptor:
    METHOD_MAPPER = {
        # Basic Python types
        str: "str",
        bool: "bool",
        float: "float",
        int: "int",
        list: "list",
        tuple: "tuple",
        dict: "dict",
        path_type: "str",
        # Special methods
        "json": "json",
        "path": "path",
        "db_url": "db_url",
        "cache_url": "cache_url",
        "search_url": "search_url",
        "email_url": "email_url",
    }

    def __init__(self, default, type=None, name=None, **kwargs):
        self.default = default
        self.name = name
        self.kwargs = kwargs

        if type is None:
            type = default.__class__
        if type not in self.METHOD_MAPPER:
            raise ValueError(f"invalid type: {type}")
        self.type = type

    def __set_name__(self, owner, name):
        prefix = getattr(owner, "env_prefix", "")
        if self.name is None:
            self.name = prefix + name
        elif "{" in self.name:
            self.name = name.format(prefix=prefix, attr=name)

    def __get__(self, instance, cls=None):
        if instance is None:
            return self
        value = self.get_value(instance)
        setattr(instance, self.name, value)
        return value

    def get_value(self, conf):
        method = self.get_env_method(conf)
        return method(self.name, default=self.default, **self.kwargs)

    def get_env_method(self, conf):
        method = self.METHOD_MAPPER[self.type]
        return getattr(conf.env, method)


class EnvProperty(EnvDescriptor):
    def __init__(self, fget, default=None, **kwargs):
        self.fget = fget
        super().__init__(default=default, **kwargs)

    def get_value(self, conf):
        value = super().get_value(conf)
        return self.fget(conf, value)


class Env(environ.Env):
    def __call__(self, name, default=None, type=None, **kwargs):
        if type is None and default is None:
            type = str
        elif type is None:
            type = default.__class__

        method_name = EnvDescriptor.METHOD_MAPPER[type]
        method = getattr(self, method_name)
        return method(name, default=default, **kwargs)
