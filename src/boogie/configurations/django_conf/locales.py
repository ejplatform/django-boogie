from .paths import PathsConf
from ..descriptors import env_property


class LocaleConf(PathsConf):
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


def country(country, locale_name, language_code, timezone, **kwargs):
    """
    Return a function that creates a LocaleConf subclass specialized for a
    given country.

    This function return a factory rather than the Conf subclass itself to avoid
    the overhead of class creation for a big list of countries.
    """
    ns = {
        'LOCALE_NAME': locale_name,
        'LANGUAGE_CODE': language_code,
        'TIMEZONE': timezone,
        **{k.upper(): v for k, v in kwargs.items()}
    }
    return lambda: type(country + 'Locale', (LocaleConf,), ns)


brazil = country('Brazil', 'pt_BR', 'pt-br', 'America/Sao_Paulo')
