from .environment import EnvironmentConf
from ..descriptors import env_property, env
from ..tools import secret_hash


class SecurityConf(EnvironmentConf):
    """
    Security options.
    """

    def finalize(self, settings):
        settings = super().finalize(settings)
        if settings['SECRET_KEY'] is None:
            settings['SECRET_KEY'] = secret_hash(settings)
        return settings

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

    ALLOWED_HOSTS = env([])

    def get_password_hashers(self):
        if self.ENVIRONMENT == 'testing':
            return [
                'django.contrib.auth.hashers.MD5PasswordHasher',
            ]
        return [
            'django.contrib.auth.hashers.Argon2PasswordHasher',
            'django.contrib.auth.hashers.PBKDF2PasswordHasher',
            'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
            'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
            'django.contrib.auth.hashers.BCryptPasswordHasher',
        ]
