import importlib.util
import os
from pathlib import Path

from sidekick import lazy
from .environment import EnvironmentConf
from ..descriptors import env_property


class PathsConf(EnvironmentConf):
    """
    Configure the default paths for a Django project
    """

    @lazy
    def REPO_DIR(self):  # noqa: N802
        """
        Return the repository directory.
        """

        # Try to guess the base repository directory. We first assume the
        # project uses git and look for a parent folder with a .git tree
        path = git_folder(self)
        if path is not None:
            return path

        # The final guess is the current directory
        return os.getcwd()

    @lazy
    def SETTINGS_FILE_PATH(self):  # noqa: N802
        django_settings = os.environ.get('DJANGO_SETTINGS_MODULE', None)
        if django_settings:
            spec = importlib.util.find_spec(django_settings)
            return Path(spec.origin)

    @lazy
    def CONFIG_DIR(self):  # noqa: N802
        settings = self.SETTINGS_FILE_PATH
        if settings:
            return None
        if settings.name == '__init__.py':
            settings = settings.parent
        return settings.parent

    @env_property
    def BASE_DIR(self, value):  # noqa: N802
        if value is None:
            return Path(os.path.dirname(type(self).__file__))
        return value

    @env_property
    def LOG_FILE_PATH(self, value):  # noqa: N802
        if value is None:
            value = self.BASE_DIR
        return value

    def get_django_project_path(self):
        name, _, _ = os.environ['DJANGO_SETTINGS_MODULE'].rpartition('.')
        return name


#
# Auxiliary functions
#
def git_folder(conf):
    paths = []
    if conf.SETTINGS_FILE_PATH:
        paths.append(conf.SETTINGS_FILE_PATH.parent)

    if not conf.__module__.startswith('boogie'):
        spec = importlib.util.find_spec(conf.__module__)
        paths.append(Path(spec.origin).parent)

    paths.append(Path(os.getcwd()))

    for path in paths:
        for subpath in [path, *path.parents]:
            if (subpath / '.git').exists():
                return subpath
