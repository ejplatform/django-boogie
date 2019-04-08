import sys

from mock import patch

# TODO: create a more exhaustive list and move to a different module.
DEFAULT_EXTERNAL_MODULES = [
    # Django
    "django",
    "django.apps",
    "django.test.client",
    "django.conf",
    "django.conf.settings",
    "django.core",
    "django.core.exceptions",
    "django.contrib",
    "django.contrib.auth",
    "django.contrib.auth.decorators",
    "django.db",
    "django.db.models",
    "django.http",
    "django.shortcuts",
    "django.test",
    "django.urls",
    "django.urls.converters",
    "django.utils",
    "django.utils.translation",
    "django.views",
    "django.views.decorators",
    "django.views.decorators.cache",
    "django.views.decorators.clickjacking",
    "django.views.decorators.csrf",
    "django.views.decorators.gzip",
    # Rest Framework
    "rest_framework",
    "rest_framework.decorators",
    "rest_framework.relations",
    "rest_framework.response",
    "rest_framework.serializers",
    "rest_framework.utils",
    "rest_framework.utils.encoders",
    "rest_framework.viewsets",
    # Scientific
    "numpy",
    "pandas",
    # Tools
    "pytest",
    "faker",
    "model_mommy",
    "model_mommy.mommy",
    "factory",
    "factory.declarations",
]


class LightMock:
    """
    A lightweight Mock class.

    It creates attributes and methods on-demand.

    >>> x = LightMock()
    >>> x.foo.bar(42)                                      # doctests: +ELLIPSIS
    <LightMock ...>
    """

    def __init__(self, *args, **kwargs):
        pass

    __method = lambda self, *args, **kwargs: LightMock()
    __call__ = __method
    __getattr__ = __method
    ___name__ = ___qualname__ = "mock"

    # Container interface
    __getitem__ = __method
    __iter__ = lambda self: iter(())

    # Arithmetic operations
    __add__ = __sub__ = __mul__ = __truediv__ = __floordiv__ = __method
    __radd__ = __rsub__ = __rmul__ = __rtruediv__ = __rfloordiv__ = __method

    # Conversions
    __bool__ = lambda self: True

    # Pretend to be a type in some situations
    __mro_entries__ = lambda *args: (object,)
    __getstate__ = lambda self: ()


def mock_save(model, method=LightMock):
    """
    Context manager that mocks the .save() method of a model to prevent it from
    hitting the database.

    Usage:
        .. code-block:: python

            with mock_save(model):
                model.name = "Hello"
                model.save()  # it does not actually touch the db
    """
    return patch.object(model, "save", LightMock)


_stdout = sys.stdout


def mock_modules(*modules):
    """
    Save all given modules that were not imported in sys.modules.
    """

    cls = type("MockItem", (LightMock, type), {})

    if modules == ("auto",):
        modules = DEFAULT_EXTERNAL_MODULES

    def path_hook(path):
        base = path.partition(".")[0]
        if base in modules:
            # It mocks all its way through a mocked module In python import
            # subsystem. This hack makes the implementation much simpler :)
            return cls()
        else:
            raise ImportError

    sys.path_hooks.insert(0, path_hook)

    for mod in modules:
        sys.modules.setdefault(mod, LightMock())


def assume_unique(form=None):
    """
    Context manager that suppress checks of uniqueness during model validation.

    Usage:
        .. code-block:: python

            with assume_unique(model):
                model.slug = "repeated-slug"
                model.full_clean()  # prevents touching the db on uniqueness checks
    """
    from django import forms

    if form is None:
        form = forms.ModelForm
    return patch.object(form, "validate_unique", no_op)


#
# Auxiliary functions
#
no_op = lambda *args, **kwargs: None
cte = lambda cte: lambda *args, **kwargs: cte


def raise_exception(exception):
    """
    Return a function that raises the given exception when called.
    """
    if exception is not None:

        def action(*args, **kwargs):
            raise exception

    else:
        action = no_op
    return action
