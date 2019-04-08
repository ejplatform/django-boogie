from .environment import EnvironmentConf
from ..descriptors import env_settings


def default(value):
    return env_settings(default=value)(lambda self, env: env)


class UrlsConf(EnvironmentConf):
    """
    Configure urls for your Django project.
    """

    get_admin_url = default("/admin/")
    get_login_url = default("/login/")
    get_logout_url = default("/account/logout/")
    get_static_url = default("/static/")
    get_media_url = default("/media/")

    def get_append_slash(self):
        return True

    @env_settings(default=None)
    def get_root_urlconf(self, env):
        return env or self.get_django_project_path() + ".urls"
