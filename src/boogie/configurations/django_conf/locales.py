import os

from .paths import PathsConf
from ..descriptors import env

# Map country on default configurations.
COUNTRY_DB = {None: {"LANGUAGE_CODE": "en-us", "TIME_ZONE": "Greenwich"}}
COUNTRY_DB[""] = COUNTRY_DB[None]


class LocaleConf(PathsConf):
    """
    Base Django locale configuration.
    """

    USE_I18N = env(True)
    USE_L10N = env(True)
    USE_TZ = env(True)
    COUNTRY = env("", name="{attr}")

    def get_language_code(self, country):
        return country_method("language_code", country)

    def get_time_zone(self, country):
        return country_method("time_zone", country)

    def get_locale_name(self, language_code, country):
        try:
            return country_method("locale_name", country)
        except ValueError:
            if language_code:
                lang, country = language_code.split("-")
                return f"{lang}_{country.upper()}.UTF8"
            else:
                return ""

    def get_locale_paths(self):
        path = os.path.join(self.REPO_DIR, "locale")
        return self.env("LOCALE_PATH", type=list, default=[path])


class NoLocaleConf(PathsConf):
    """
    Base configuration for instances that do not use localization.
    """

    USE_I18N = env(False)
    USE_L10N = env(False)
    USE_TZ = False
    LANGUAGE_CODE = None
    TIME_ZONE = None


def country_method(var, country):
    django_var = "DJANGO_" + var.upper()
    key = var.upper()
    if django_var in os.environ:
        return os.environ[django_var]
    try:
        return COUNTRY_DB[country.upper()][key]
    except KeyError as exc:
        raise ValueError(f"{exc}: unknown for country {country}")


#
# Register countries
#
def country(country: list, language_code, timezone):
    """
    Return a function that creates a LocaleConf subclass specialized for a
    given country.

    This function return a factory rather than the Conf subclass itself to avoid
    the class creation overhead of a big list of countries.
    """
    names = [country] if isinstance(country, str) else country
    for alias in names:
        COUNTRY_DB[alias.upper()] = {
            "LANGUAGE_CODE": language_code,
            "TIME_ZONE": timezone,
        }


# Ursal
country(["Argentina"], "es-ar", "America/Buenos_Aires")
country(["Bolívia"], "es-bo", "America/La_Paz")
country(["Brasil", "Brazil"], "pt-br", "America/Sao_Paulo")
country(["Chile"], "es-cl", "America/Santiago")
country(["Ecuador"], "es-ec", "America/Guayaquil")
country(["Paraguay"], "es-py", "America/Asuncion")
country(["Peru"], "es-pe", "America/Lima")
country(["Uruguay"], "es-uy", "America/Montevideo")
country(["Venezuela"], "es-ve", "America/Caracas")

# Other american countries

# Africa

# Asia

# Europe

# Oceania
