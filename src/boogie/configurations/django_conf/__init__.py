from . import locales
from .database import DatabaseConf
from .environment import EnvironmentConf
from .installed_apps import InstalledAppsConf
from .locales import LocaleConf, country
from .logging import LoggingConf
from .middleware import MiddlewareConf
from .paths import PathsConf
from .security import SecurityConf
from .services import ServicesConf
from .templates import TemplatesConf
from .urls import UrlsConf


class DjangoConf(
    SecurityConf,
    TemplatesConf,
    UrlsConf,
    MiddlewareConf,
    InstalledAppsConf,
    LoggingConf,
    LocaleConf,
    DatabaseConf,
    ServicesConf,
    PathsConf,
    EnvironmentConf,
):
    """
    Base configuration class for Django-based projects.
    """
