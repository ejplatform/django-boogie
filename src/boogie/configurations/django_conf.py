import os
from pathlib import Path

from sidekick import unique

from .base import Conf
from .descriptors import env, env_property
from .tools import secret_hash


class BaseConf(Conf):
    """
    Base class for Django configurations. Users should use DjangoConf
    """

    env_prefix = 'DJANGO_'

    def finalize(self, settings):
        settings = super().finalize(settings)
        if settings['SECRET_KEY'] is None:
            settings['SECRET_KEY'] = secret_hash(settings)
        return settings

    #: Django base environment. We suggest distinguishing between 'local',
    #: 'test' and 'production'.
    ENVIRONMENT = env('local')

    #: WARNING: keep the secret key used in production secret! We generate a
    #: secret from a hash of the current settings during the .finalize() phase.
    #: this is ok for local development, but may be insecure/inconvenient for
    #: production.
    @env_property
    def SECRET_KEY(self, value):  # noqa: N802
        if value is None:
            if self.ENVIRONMENT in ('local', 'test'):
                return self.ENVIRONMENT
            else:
                return None
        return value

    #: Build paths inside the project like this: BASE_DIR / 'foo'
    @env_property
    def BASE_DIR(self, value):  # noqa: N802
        if value is None:
            conf_dir = Path(os.path.dirname(type(self).__file__))

            return conf_dir
        return value

    #: Location of the django project
    @property
    def django_project_path(self):
        name, _, _ = os.environ['DJANGO_SETTINGS_MODULE'].rpartition('.')
        return name

    #: By default, debug is enabled only on 'local' and 'test' environments.
    @env_property(type=bool)
    def DEBUG(self, value):  # noqa: N802
        if value is None:
            return self.ENVIRONMENT in ('test', 'local')
        return value

    ALLOWED_HOSTS = env([])

    # Database
    # https://docs.djangoproject.com/en/2.0/ref/settings/#databases
    DATABASES = env('sqlite:///db.sqlite3', type='db_url')

    # Password validation
    # https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators
    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ]

    @env_property
    def ROOT_URLCONF(self, value):  # noqa: N802
        if value is None:
            return self.django_project_path + '.urls'
        return value

    @env_property
    def WSGI_APPLICATION(self, value):  # noqa: N802
        if value is None:
            return self.django_project_path + '.wsgi.application'
        return value

    # Internationalization
    # https://docs.djangoproject.com/en/2.0/topics/i18n/
    LANGUAGE_CODE = env('en-us')
    TIME_ZONE = env('UTC')
    USE_I18N = env(True)
    USE_L10N = env(True)
    USE_TZ = env(True)

    #: Static files (CSS, JavaScript, Images)
    #: https://docs.djangoproject.com/en/2.0/howto/static-files/
    STATIC_URL = env('/static/')

    #: It is often convenient to enable/disable Django ability to serve static
    #: files.
    SERVE_STATIC_FILES = env(True)

    #: Site admin url, if Django admin app is installed.
    ADMIN_URL = env('admin/')


class InstalledAppsConf(BaseConf):
    """
    Mixin class that helps managing INSTALLED_APPS.
    """

    INSTALLED_APPS = property(lambda self: self.get_installed_apps())  # noqa: N802

    disable_django_users = False
    disable_django_admin = False
    extra_contrib_apps = []
    third_party_apps = []
    project_apps = []

    def get_installed_apps(self):
        """
        Return a list of installed apps.

        The list contains project  apps + thirdy parties + contrib, in that
        order.
        """
        return list(unique([
            *self.get_project_apps(),
            *self.get_third_party_apps(),
            *self.get_contrib_apps(),
        ]))

    def get_project_apps(self):
        """
        Return a list of apps created specifically for the project.
        """
        return list(self.project_apps)

    def get_third_party_apps(self):
        """
        Return a list of third party dependencies.
        """
        return list(self.third_party_apps)

    def get_contrib_apps(self):
        """
        Return a list of apps from django.contrib.
        """

        apps = list(self.extra_contrib_apps)
        if not self.disable_django_admin:
            apps.append('django.contrib.admin')
        if not self.disable_django_users:
            apps.extend(['django.contrib.auth', 'django.contrib.sessions'])
        apps.extend(['django.contrib.contenttypes', 'django.contrib.messages'])
        if self.SERVE_STATIC_FILES:
            apps.append('django.contrib.staticfiles')
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


class MiddlewareConf(InstalledAppsConf):
    """
    Configure middleware classes.
    """

    MIDDLEWARE = property(lambda self: self.get_middleware())
    with_middleware = InstalledAppsConf.with_app

    def get_middleware(self):
        apps = self.INSTALLED_APPS

        def add(middleware):
            if middleware.partition('.middleware')[0] in apps:
                return [middleware]
            else:
                return []

        return [
            'django.middleware.security.SecurityMiddleware',
            *add('django.contrib.sessions.middleware.SessionMiddleware'),
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            *add('django.contrib.auth.middleware.AuthenticationMiddleware'),
            *add('django.contrib.messages.middleware.MessageMiddleware'),
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ]


class TemplatesConf(BaseConf):
    """
    Configure templates.
    """

    @property
    def TEMPLATES(self):  # noqa: N802
        return [self.DJANGO_TEMPLATES, self.JINJA_TEMPLATES]

    DJANGO_TEMPLATES = {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    }

    JINJA_TEMPLATES = {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {}
    }


class DjangoConf(MiddlewareConf,
                 TemplatesConf,
                 InstalledAppsConf,
                 BaseConf):
    """
    Base configuration class for Django-based projects.
    """
