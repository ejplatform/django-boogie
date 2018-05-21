from .paths import PathsConf


class LoggingConf(PathsConf):
    """
    Base configurations for logging.
    """

    DEBUG_LOGGER = {
        'handlers': ['console'],
        'level': 'DEBUG',
        'propagate': True,
    }
    DEFAULT_LOGGER = {
        'handlers': ['console'],
        'level': 'INFO',
        'propagate': True,
    }

    @property
    def LOGGING_CONSOLE_HANDLER(self):  # noqa: N802
        return {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        }

    @property
    def LOGGING_FILE_HANDLER(self):  # noqa: N802
        return {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': self.LOG_FILE_PATH,
        }

    @property
    def LOGGING(self):  # noqa: N802
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'handlers': {
                'file': self.LOGGING_CONSOLE_HANDLER,
                'console': self.LOGGING_FILE_HANDLER,
            },
            'loggers': {
                'ej': self.DEBUG_LOGGER,
                'django': self.DEFAULT_LOGGER,
                'celery': self.DEFAULT_LOGGER,
            },
        }
