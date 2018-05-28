from ..base import Conf
from ..descriptors import env, env_property


class EnvironmentConf(Conf):
    """
    Base class for Django configurations. Users should use DjangoConf
    """

    env_prefix = 'DJANGO_'

    #: Django base environment. We suggest distinguishing between 'local',
    #: 'test' and 'production'.
    ENVIRONMENT = env('local')

    #: By default, debug is enabled only on 'local' and 'test' environments.
    @env_property(type=bool)
    def DEBUG(self, value):  # noqa: N802
        if value is None:
            return self.ENVIRONMENT == 'local'
        return value

    @env_property
    def WSGI_APPLICATION(self, value):  # noqa: N802
        if value is None:
            return self.get_django_project_path() + '.wsgi.application'
        return value

    # Internationalization
    # https://docs.djangoproject.com/en/2.0/topics/i18n/
    LANGUAGE_CODE = env('en-us')
    TIME_ZONE = env('UTC')
    USE_I18N = env(True)
    USE_L10N = env(True)
    USE_TZ = env(True)

    #: It is often convenient to enable/disable Django ability to serve static
    #: files.
    SERVE_STATIC_FILES = env(True)

    #: Site admin url, if Django admin app is installed.
    SITE_ID = 1

    #: Authentication
    AUTH_USER_MODEL = 'auth.User'
