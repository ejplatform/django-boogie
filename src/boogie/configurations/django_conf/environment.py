from django.core.exceptions import ImproperlyConfigured

from ..base import Conf
from ..descriptors import env_settings, env_default


class EnvironmentConf(Conf):
    """
    Base class for Django configurations. Users should use DjangoConf
    """

    env_prefix = "DJANGO_"

    def get_environment(self, env="local"):
        """
        Django base environment. We suggest distinguishing between 'local',
        'test' and 'production'.
        """
        if env not in ["test", "production", "local"]:
            raise ImproperlyConfigured(f"Invalid environment: {env}")
        return env

    @env_settings(type=bool, default=None)
    def get_debug(self, env):
        """
        By default, debug is enabled only on 'local' and 'test' environments.
        """
        if env is None:
            return self.ENVIRONMENT == "local"
        return env

    @env_default()
    def get_wsgi_application(self):
        return self.DJANGO_PROJECT_PATH + ".wsgi.application"

    @env_default()
    def get_site_id(self):
        """
        Site admin url, if Django admin app is installed.
        """
        return 1

    def get_serve_static_files(self):
        """
        It is often convenient to enable/disable Django ability to serve static
        files.
        """
        return True

    def get_auth_user_model(self):
        return "auth.User"
