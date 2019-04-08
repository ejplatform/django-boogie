import importlib.util
import os
from pathlib import Path

from .environment import EnvironmentConf


class PathsConf(EnvironmentConf):
    """
    Configure the default paths for a Django project
    """

    def get_repo_dir(self):
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

    def get_settings_file_path(self):
        django_settings = os.environ.get("DJANGO_SETTINGS_MODULE", None)
        if django_settings:
            spec = importlib.util.find_spec(django_settings)
            return Path(spec.origin)

    def get_config_dir(self):
        settings = self.SETTINGS_FILE_PATH
        if settings:
            return None
        if settings.name == "__init__.py":
            settings = settings.parent
        return settings.parent

    def get_base_dir(self):
        return get_dir(self)

    def get_log_file_path(self):
        value = self.env("DJANGO_LOG_FILE_PATH", default=None)
        if value is None:
            value = self.BASE_DIR / "logfile.log"
        return value

    def get_django_project_path(self):
        name, _, _ = os.environ["DJANGO_SETTINGS_MODULE"].rpartition(".")
        return name


#
# Auxiliary functions
#
def git_folder(conf):
    paths = []
    if conf.SETTINGS_FILE_PATH:
        paths.append(conf.SETTINGS_FILE_PATH.parent)

    if not conf.__module__.startswith("boogie"):
        spec = importlib.util.find_spec(conf.__module__)
        paths.append(Path(spec.origin).parent)

    paths.append(Path(os.getcwd()))

    for path in paths:
        for subpath in [path, *path.parents]:
            if (subpath / ".git").exists():
                return subpath


def get_dir(conf):
    spec = importlib.util.find_spec(conf.__module__)
    return Path(spec.origin).parent
