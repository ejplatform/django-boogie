from .descriptors import env, env_settings, env_default
from .base import Conf, save_configuration
from .django_conf import (
    DjangoConf,
    EnvironmentConf,
    InstalledAppsConf,
    MiddlewareConf,
    TemplatesConf,
    SecurityConf,
    PathsConf,
    UrlsConf,
    ServicesConf,
    LoggingConf,
    locales,
)
