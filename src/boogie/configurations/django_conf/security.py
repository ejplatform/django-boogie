from .environment import EnvironmentConf
from ..tools import secret_hash


class SecurityConf(EnvironmentConf):
    """
    Security options.
    """

    def finalize(self, settings):
        settings = super().finalize(settings)
        if not settings.get("SECRET_KEY"):
            settings["SECRET_KEY"] = secret_hash(settings)
        return settings

    def get_secret_key(self):
        """
        WARNING: keep the secret key used in production secret! We generate a
        secret from a hash of the current settings during the .finalize() phase.
        this is ok for local development, but may be insecure/inconvenient for
        """
        value = self.env.str("DJANGO_SECRET_KEY", default=None)
        if not value:
            if self.ENVIRONMENT in ("local", "test"):
                return self.ENVIRONMENT
            else:
                return None
        return value

    # https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators
    def get_auth_password_validators(self):
        """
        Password validation
        """
        prefix = "django.contrib.auth.password_validation"
        validators = [
            "UserAttributeSimilarityValidator",
            "MinimumLengthValidator",
            "CommonPasswordValidator",
            "NumericPasswordValidator",
        ]
        return [{"NAME": f"{prefix}.{x}"} for x in validators]

    def get_allowed_hosts(self):
        return self.env("DJANGO_ALLOWED_HOSTS", type=list, default=["localhost"])

    def get_password_hashers(self):
        if self.ENVIRONMENT == "testing":
            return ["django.contrib.auth.hashers.MD5PasswordHasher"]
        return [
            "django.contrib.auth.hashers.Argon2PasswordHasher",
            "django.contrib.auth.hashers.PBKDF2PasswordHasher",
            "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
            "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
            "django.contrib.auth.hashers.BCryptPasswordHasher",
        ]
