from .environment import EnvironmentConf
from ..descriptors import env, env_property


class UrlsConf(EnvironmentConf):
    """
    Configure urls for your Django project.
    """

    ADMIN_URL = env('admin/')
    LOGIN_URL = env('/login/')
    LOGOUT_URL = env('/logout/')
    STATIC_URL = env('/static/')
    MEDIA_URL = env('/media/')

    @env_property
    def ROOT_URLCONF(self, value):  # noqa: N802
        if value is None:
            return self.get_django_project_path() + '.urls'
        return value

    APPEND_SLASH = True
