import os
import sys
from importlib import import_module

from django.core.exceptions import ImproperlyConfigured

from .descriptors import Env


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
            where = os.environ['DJANGO_SETTINGS_MODULE']
        except KeyError:
            raise ImproperlyConfigured(
                'You must either define the DJANGO_SETTINGS_MODULE environment '
                'variable or pass an explicit module name to the '
                'init_configuration function.'
            )
    if isinstance(where, str):
        where = import_module(where).__dict__
    elif isinstance(where, type(sys)):
        where = where.__dict__

    # We create an instance of the class configuration and import all symbols
    # with upper case names.
    conf = conf_class()
    where.update(conf.get_settings())


class Conf:
    """
    Base class for all configuration classes.
    """

    ENVFILE = None
    env_prefix = ''

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
        for attr, value in kwargs.items():
            attr = attr.upper()
            if hasattr(cls, attr):
                setattr(self, attr, value)
            else:
                raise TypeError(f'invalid argument: {attr}')

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

    def get_settings(self):
        """
        Return a dictionary with all settings defined by the configuration.

        This method is idempotent. It caches the resulting settings and always
        return the same settings dictionary.
        """
        if self._settings is None:
            self.prepare()
            settings = {
                attr: getattr(self, attr, None)
                for attr in dir(self)
                if (attr.isupper() and not attr.startswith('_'))
            }
            if settings.get('ENVFILE') is None:
                settings.pop('ENVFILE', None)
            self._settings = self.finalize(settings)
        return dict(self._settings)
