from boogie.configurations import django_conf
from boogie.configurations.django_conf import DjangoConf


class LoggingConf(django_conf.LoggingConf):
    """
    Same as default config.
    """


class UrlsConf(django_conf.UrlsConf):
    """
    Same as default config.
    """


class PathsConf(django_conf.PathsConf):
    """
    Same as default config.
    """


class TemplatesConf(django_conf.TemplatesConf):
    """
    Same as default config.
    """


class EnvironmentConf(django_conf.EnvironmentConf):
    """
    Same as default config.
    """


class ServicesConf(django_conf.ServicesConf):
    """
    Same as default config.
    """


class SecurityConf(django_conf.SecurityConf):
    """
    Same as default config.
    """


class InstalledAppsConf(django_conf.InstalledAppsConf):
    """
    Install the following apps:
    * Django Rest Framework apps

    Plus:
    * Install Django Debug Toolbar in local environment.
    """

    def get_third_party_apps(self):
        apps = super().get_third_party_apps()
        if self.ENVIRONMENT == "local":
            apps = ["debug_toolbar", *apps, "django_extensions"]
        return apps


class MiddlewareConf(django_conf.MiddlewareConf):
    """
    Changes:
    * Install Django debug toolbar middleware in local enviroment.
    """


class BoogieConf(
    DjangoConf,
    SecurityConf,
    TemplatesConf,
    UrlsConf,
    MiddlewareConf,
    InstalledAppsConf,
    LoggingConf,
    ServicesConf,
    PathsConf,
    EnvironmentConf,
):
    """
    Base configuration for the Boogie stack.

    See each layer of configuration to see the changes introduced by the
    Boogie stack.
    """
