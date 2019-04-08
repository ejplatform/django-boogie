import os

from boogie.configurations.tools import module_exists
from .paths import PathsConf


class TemplatesConf(PathsConf):
    """
    Configure templates.
    """

    def get_templates(self):
        templates = [self.DJANGO_TEMPLATES, self.JINJA_TEMPLATES]
        return [x for x in templates if x]

    #
    # DJANGO TEMPLATES
    #
    def get_django_templates(self):
        return {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": self.DJANGO_TEMPLATES_DIRS,
            "APP_DIRS": True,
            "OPTIONS": {"context_processors": self.DJANGO_CONTEXT_PROCESSORS},
        }

    def get_django_context_processors(self):
        return [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
        ]

    #
    # JINJA2 TEMPLATES
    #
    def get_jinja_templates(self):
        options = {}
        env = self.JINJA_ENVIRONMENT
        if env is not None:
            options["environment"] = env
        return {
            "BACKEND": "django.template.backends.jinja2.Jinja2",
            "DIRS": self.JINJA_TEMPLATES_DIRS,
            "APP_DIRS": True,
            "OPTIONS": {"extensions": self.JINJA_EXTENSIONS, **options},
        }

    def get_django_templates_dirs(self):
        return []

    def get_jinja_templates_dirs(self):
        return []

    def get_jinja_extensions(self):
        return ["jinja2.ext.i18n"]

    def get_jinja_environment(self):
        base, _, end = os.environ["DJANGO_SETTINGS_MODULE"].rpartition(".")
        module = base + ".jinja2"
        if module_exists(module):
            return module + ".environment"
        return "boogie.jinja2.boogie_environment"
