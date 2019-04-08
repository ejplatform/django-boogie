import importlib.util

from sidekick import unique
from .environment import EnvironmentConf


class InstalledAppsConf(EnvironmentConf):
    """
    Mixin class that helps managing INSTALLED_APPS.
    """

    def get_use_django_users(self):
        return True

    def get_use_django_admin(self):
        return True

    def get_installed_apps(self):
        """
        Return a list of installed apps.

        The list contains project  apps + thirdy parties + contrib, in that
        order.
        """
        return list(
            unique(
                filter(
                    lambda x: x is not None,
                    [
                        *self.PROJECT_APPS,
                        *self.THIRD_PARTY_APPS,
                        *self.DJANGO_CONTRIB_APPS,
                    ],
                )
            )
        )

    def get_project_apps(self):
        """
        Return a list of apps created specifically for the project.
        """
        return []

    def get_third_party_apps(self):
        """
        Return a list of third party dependencies.
        """
        return []

    def get_django_contrib_apps(self):
        """
        Return a list of apps from django.contrib.
        """

        apps = []
        if self.USE_DJANGO_ADMIN:
            apps.append("django.contrib.admin")
        if self.USE_DJANGO_USERS:
            apps.extend(["django.contrib.auth", "django.contrib.sessions"])
        apps.extend(
            [
                "django.contrib.contenttypes",
                "django.contrib.messages",
                "django.contrib.sites",
            ]
        )
        if self.SERVE_STATIC_FILES:
            apps.append("django.contrib.staticfiles")
        return apps

    def with_app(self, app, app_list, deps=None, optdeps=None):
        """
        Insert app on list, respecting its dependencies.

        Usage:
            Useful for third parties declare dependency classes:

            class MyAppConf(InstalledAppsConf):
                def get_third_party_apps(self):
                    apps = super().get_third_party_apps()
                    return self.with_app('my_app', apps, deps=['dep1', 'dep2'])

        Args:
            app:
                App name.
            app_list:
                List of apps.
            deps:
                List of hard dependencies. All apps in that list are also
                inserted in the result just after the inserted app.
            optdeps:
                List of optional dependencies. App will be inserted just
                before all apps in list if they appear in the app list.

        Returns:
            A list of apps.
        """
        apps = [app]
        apps.extend(x for x in (deps or ()) if x not in app_list)
        all_deps = set(deps or ())
        all_deps.update(optdeps or ())

        result = []
        for app in app_list:
            if apps and app in all_deps:
                result.extend(apps)
                apps = None
            result.append(app)
        return result

    @staticmethod
    def filter_installed_apps(apps):
        """
        Return only the installed apps in the following list.

        Each item may be either a string with the app name or a tuple/list with
        the app name followed by all of its dependencies.
        """
        filtered = []
        is_installed = lambda dep: importlib.util.find_spec(dep) is not None

        for app in apps:
            if isinstance(app, (tuple, list)):
                app, *deps = app
            else:
                app = deps = app
            if all(is_installed(dep) for dep in deps):
                filtered.append(app)

        return filtered
