from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from .paths import PathsConf


class LoggingConf(PathsConf):
    """
    Base configurations for logging.
    """

    def get_debug_logger(self):
        return {"handlers": ["console", "file"], "level": "DEBUG", "propagate": True}

    def get_default_logger(self):
        return {"handlers": ["console", "file"], "level": "INFO", "propagate": True}

    def get_logging_console_handler(self):
        return {"level": "DEBUG", "class": "logging.StreamHandler"}

    def get_logging_file_handler(self):
        path = Path(self.LOG_FILE_PATH)
        if path.is_dir():
            raise ImproperlyConfigured(
                "log file is a directory. Please set a correct LOG_FILE_PATH "
                "in your configuration file that points to a log file, instead "
                "of a directory."
            )
        return {"level": "DEBUG", "class": "logging.FileHandler", "filename": path}

    def get_logging(self):  # noqa: N802
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "handlers": {
                "file": self.LOGGING_FILE_HANDLER,
                "console": self.LOGGING_CONSOLE_HANDLER,
            },
            "loggers": {"django": self.DEFAULT_LOGGER, "celery": self.DEFAULT_LOGGER},
        }
