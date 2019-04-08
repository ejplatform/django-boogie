from functools import wraps

from django.db import models
from django.utils.translation import ugettext_lazy as _
from sidekick import import_later

autoslug = import_later("autoslug")


def label(value):
    """
    Add default label to field function.
    """

    def decorator(func):
        @wraps(func)
        def decorated(verbose_name=value, *args, **kwargs):
            return func(verbose_name, *args, **kwargs)

        return decorated

    return decorator


def max_length(name, default=140):
    """
    Reads max_length property from settings.
    """
    return arg_from_settings("max_length", name, default)


def arg_from_settings(prop, name, default=None):
    """
    Read argument from settings file.
    """

    def decorator(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            if prop not in kwargs:
                from django.conf import settings

                kwargs[prop] = getattr(settings, name, default)
            return func(*args, **kwargs)

        return decorated

    return decorator


# noinspection PyPep8Naming
@label(_("slug"))
def AutoSlugField(*args, **kwargs):  # noqa: N802
    return autoslug.AutoSlugField(*args, **kwargs)


# noinspection PyPep8Naming
@label(_("name"))
@max_length("NAME_MAX_LENGTH", 40)
def NameField(*args, **kwargs):  # noqa: N802
    return models.CharField(*args, **kwargs)


# noinspection PyPep8Naming
@label(_("title"))
@max_length("TITLE_MAX_LENGTH", 140)
def TitleField(*args, **kwargs):  # noqa: N802
    return models.CharField(*args, **kwargs)


# noinspection PyPep8Naming
@label(_("description"))
@max_length("SHORT_DESCRIPTION_MAX_LENGTH", 255)
def ShortDescriptionField(*args, **kwargs):  # noqa: N802
    kwargs.setdefault("help_text", _("Conscise description used on listings."))
    return models.CharField(*args, **kwargs)


# noinspection PyPep8Naming
@label(_("detailed description"))
def LongDescriptionField(*args, **kwargs):  # noqa: N802
    kwargs.setdefault("help_text", _("Detailed description of object."))
    return models.TextField(*args, **kwargs)
