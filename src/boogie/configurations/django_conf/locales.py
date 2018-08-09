import os

from .paths import PathsConf
from ..descriptors import env

# Map country on default configurations.
COUNTRY_DB = {
    None: {
        'LOCALE_NAME': 'en_US',
        'LANGUAGE_CODE': 'en-us',
        'TIME_ZONE': 'Greenwich',
    },
}
COUNTRY_DB['USA'] = COUNTRY_DB[None]


def country_method(var):
    django_var = 'DJANGO_' + var.upper()
    key = var.upper()

    def country_method(self, value):
        try:
            return os.environ[django_var]
        except KeyError:
            return COUNTRY_DB[value.upper()][key]

    country_method.__name__ = country_method.__qualname__ = var.lower()

    return country_method


class LocaleConf(PathsConf):
    """
    Base Django locale configuration.
    """
    USE_I18N = env(True)
    USE_L10N = env(True)
    USE_TZ = env(True)
    COUNTRY = env('', name='{attr}')

    get_locale_path = country_method('locale_path')
    get_locale_name = country_method('locale_name')
    get_time_zone = country_method('time_zone')


class NoLocalConf(PathsConf):
    """
    Base configuration for instances that do not use localization.
    """
    USE_I18N = env(False)
    USE_L10N = env(False)
    USE_TZ = False
    LOCALE_NAME = None
    LANGUAGE_CODE = None
    TIME_ZONE = None


#
# Register countries
#
def country(country: list, locale_name, language_code, timezone):
    """
    Return a function that creates a LocaleConf subclass specialized for a
    given country.

    This function return a factory rather than the Conf subclass itself to avoid
    the class creation overhead of a big list of countries.
    """
    names = [country] if isinstance(country, str) else country
    for alias in names:
        COUNTRY_DB[alias.upper()] = {
            'LOCALE_NAME': locale_name,
            'LANGUAGE_CODE': language_code,
            'TIMEZONE': timezone,
            'COUNTRY_NAME': country,
        }


country(['Brasil', 'Brazil'], 'pt_BR', 'pt-br', 'America/Sao_Paulo')
