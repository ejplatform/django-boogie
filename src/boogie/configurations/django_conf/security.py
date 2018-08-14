from .environment import EnvironmentConf
from ..tools import secret_hash


class SecurityConf(EnvironmentConf):
    """
    Security options.
    """

    def finalize(self, settings):
        settings = super().finalize(settings)
        if not settings.get('SECRET_KEY'):
            settings['SECRET_KEY'] = secret_hash(settings)
        return settings

    #: WARNING: keep the secret key used in production secret! We generate a
    #: secret from a hash of the current settings during the .finalize() phase.
    #: this is ok for local development, but may be insecure/inconvenient for
    def get_secret_key(self):  # noqa: N802
        value = self.env.str('DJANGO_SECRET_KEY', default=None)
        if not value:
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

    def get_allowed_hosts(self):
        return self.env('DJANGO_ALLOWED_HOSTS', type=list, default=['localhost'])

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
