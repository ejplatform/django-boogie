from .installed_apps import InstalledAppsConf


class MiddlewareConf(InstalledAppsConf):
    """
    Configure middleware classes.
    """

    with_middleware = InstalledAppsConf.with_app

    def get_middleware(self):
        apps = self.INSTALLED_APPS

        def add(middleware):
            if middleware.partition(".middleware")[0] in apps:
                return [middleware]
            else:
                return []

        return [
            "django.middleware.security.SecurityMiddleware",
            *add("django.contrib.sessions.middleware.SessionMiddleware"),
            "django.middleware.common.CommonMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            *add("django.contrib.auth.middleware.AuthenticationMiddleware"),
            *add("django.contrib.messages.middleware.MessageMiddleware"),
            "django.middleware.clickjacking.XFrameOptionsMiddleware",
        ]
