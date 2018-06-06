from .paths import PathsConf
from ..descriptors import env_property


class LocaleConf(PathsConf):
    """
    Base Django locale configuration.
    """
    USE_I18N = True
    USE_L10N = True
    USE_TZ = True
    LOCALE_NAME = 'en_US'
    LANGUAGE_CODE = 'en-us'
    TIME_ZONE = 'Greenwich'

    @env_property(type=list)
    def LOCALE_PATHS(self, value):  # noqa: N802
        if value is None:
            value = [self.REPO_DIR / 'locale']
        return value


class NoLocalConf(PathsConf):
    """
    Base configuration for instances that do not use localization.
    """
    USE_I18N = False
    USE_L10N = False
    USE_TZ = False
    LOCALE_NAME = None
    LANGUAGE_CODE = None
    TIME_ZONE = None


def country(country, locale_name, language_code, timezone, **kwargs):
    """
    Return a function that creates a LocaleConf subclass specialized for a
    given country.

    This function return a factory rather than the Conf subclass itself to avoid
    the class creation overhead of a big list of countries.
    """
    ns = {
        'LOCALE_NAME': locale_name,
        'LANGUAGE_CODE': language_code,
        'TIMEZONE': timezone,
        **{k.upper(): v for k, v in kwargs.items()}
    }
    return lambda: type(country + 'Locale', (LocaleConf,), ns)


brazil = country('Brazil', 'pt_BR', 'pt-br', 'America/Sao_Paulo')
