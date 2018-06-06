==============
Configurations
==============

Django settings.py module is often a point of a lot of friction in a Django
project. Modules are very bad to compose and not convenient to reuse. Boogie
takes inspiration on django-configurations and integrates it with django-environ
to make the settings module more manageable. The gist is that configurations are
now defined in by class inheritance and not by using modules.

Boogie also provides a few reusable configuration classes that makes it much
easier to build a new project.


Getting started
===============

.. code-block:: python

    # in your settings.py
    from boogie.configurations import Conf, env

    class Conf(Conf):
        """
        An example of configuration class showing a few options
        """

        # Straightforward variable definition
        A_SIMPLE_VARIABLE = 42

        # Properties also work as usual
        @property
        def A_PROPERTY_BASED_VARIABLE(self):
            return self.A_SIMPLE_VARIABLE + 1

        # A variable that can be overridden by an environment setting
        ENV_VARIABLE = env(42)

        # Lowercase methods starting with get_* are also interpreted as
        # variables. All expected arguments are extracted from the current
        # configuration
        def get_forty_three(self, env_variable):
            return env_variable + 1

        # Methods, lowercase variables, etc, can be used as normal, but they
        # will not be exported to the settings module.
        def compute_value(self, index):
            options = [1, 2, 3, 4]
            return options[index]

    # Save settings in the default DJANGO_SETTINGS_MODULE module
    Conf.save_settings()



A deeper dive
=============

Everything you known about standard Python class definitions apply here:
configurations can have properties, methods, can define variables during
__init__, etc. Boogie configuration classes accept all of that. The whole
process of how init_configuration works is very simple:

1) It creates an instance of the chosen configuration class.
2) It calls the .load_settings() method of that instance. This method should
   return a dictionary of settings variables.
3) It inserts all those settings in the current DJANGO_SETTINGS_MODULE module.

You can override the .load_settings() method to do whatever you want. The
default behavior, however, is like so:

1) Call the .prepare() hook of the configuration instance.
2) Create a dictionary of settings by collecting all uppercase attributes
   and their corresponding values.
3) Call the .finalize(settings) hook with the resulting settings dictionary and
   return the result.
