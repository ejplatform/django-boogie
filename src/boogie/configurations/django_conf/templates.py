import os

from boogie.configurations.tools import module_exists
from .paths import PathsConf


class TemplatesConf(PathsConf):
    """
    Configure templates.
    """

    @property
    def TEMPLATES(self):  # noqa: N802
        templates = [self.DJANGO_TEMPLATES, self.JINJA_TEMPLATES]
        return [x for x in templates if x]

    @property
    def DJANGO_TEMPLATES(self):  # noqa: N802
        return {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': self.get_django_templates_dirs(),
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

    @property
    def JINJA_TEMPLATES(self):  # noqa: N802
        options = {}
        env = self.get_jinja2_environment()
        if env is not None:
            options['environment'] = env
        return {
            'BACKEND': 'django.template.backends.jinja2.Jinja2',
            'DIRS': self.get_jinja_templates_dirs(),
            'APP_DIRS': True,
            'OPTIONS': {
                'extensions': self.get_jinja2_extensions(),
                'context_processors': self.get_jinja2_context_processors(),
                **options,
            },
        }

    def get_django_templates_dirs(self):
        return []

    def get_jinja_templates_dirs(self):
        return []

    def get_jinja2_context_processors(self):
        return []

    def get_jinja2_extensions(self):
        return ['jinja2.ext.i18n']

    def get_jinja2_environment(self):
        base, _, end = os.environ['DJANGO_SETTINGS_MODULE'].rpartition('.')
        module = base + '.jinja2'
        if module_exists(module):
            return module + '.environment'
        return 'boogie.jinja2.boogie_environment'
