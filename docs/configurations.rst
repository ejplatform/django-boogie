.. module:: boogie.configuration

==============
Configurations
==============

Django settings.py module is often a point of friction in a Django project.
Django settings are organized inside modules, but modules are very bad to
compose and not convenient to reuse. Boogie takes inspiration on
django-configurations and integrates it with django-environ to make the settings
module more manageable. The main point is that configurations are
now defined by a class structure (using inheritance) and not by setting
variables on modules.

Boogie also provides a few reusable configuration classes that makes it
easier to build a new project from scratch.


Getting started
===============

Django uses a module to define a namespace for setting configuration variables.
In Boogie configurations, we replace the module by a class:

.. code-block:: python

    # in your settings.py
    from boogie.configurations import Conf, env

    #
    # The configuration class
    #
    class Config(Conf):
        # It accepts straightforward variable definitions
        A_SIMPLE_VARIABLE = 42

        # Properties work as usual
        @property
        def A_PROPERTY_BASED_VARIABLE(self):
            return self.A_SIMPLE_VARIABLE + 1

        # Conf classes understand the env() object. Attributes declared with
        # env can be overridden by environment variables.
        ENV_VARIABLE = env(42)

        # Lowercase methods starting with get_* are also interpreted as
        # variables. All expected arguments are extracted from the current
        # configuration and passed to the function
        def get_forty_three(self, env_variable):
            return env_variable + 1

        # Methods, lowercase variables, etc, can be used as normal, but they
        # will not be exported to the settings module.
        def compute_value(self, index):
            options = [1, 2, 3, 4]
            return options[index]

    # Finally, this method saves the settings in the default
    # DJANGO_SETTINGS_MODULE module
    Config.save_settings()


The point of using classes, however, is not replacing where we define our
namespace. Classes are much more suitable for code reuse through inheritance
than flat module namespaces. The Conf base class we used above does not define
any Django-specific behavior. Boogie defines a few classes aimed specifically
at Django projects.

Django configuration
--------------------

The base class



API Documentation
=================


A deeper dive
=============

Most users don't have to read this section, but might be useful when you want
to implement a reusable configuration class. The process of extracting settings
from the class to a settings module works like so:

1) The save_settings method creates an instance of the chosen configuration
   class and calls the .load_settings() method of that instance. This method
   should return a dictionary of settings variables.
2) It inserts all variables in the current DJANGO_SETTINGS_MODULE module.

You can override the .load_settings() method to do whatever you want. The
default behavior, however, is this:

1) Call the .prepare() hook of the configuration instance.
2) Creates a dictionary of settings by collecting all uppercase attributes
   and their corresponding values.
3) Call the .finalize(settings) hook with the resulting settings dictionary and
   return the result.
