import datetime

from django.apps import apps
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _, ugettext as __
from sidekick import delegate_to, lazy

from ...functions import get_config

strptime = datetime.datetime.strptime


class UserManager(BaseUserManager):
    """
    A manager that mimics the interface of Django's default User manager.
    """

    def create_user(self, *args, username=None, commit=True, **kwargs):
        if username is not None:
            kwargs["alias"] = username
        new = self.model(**kwargs)
        new.set_password(kwargs.get("password"))
        if commit:
            new.save()
        return new

    def create_superuser(self, *args, commit=True, **kwargs):
        user = self.create_user(*args, commit=False, **kwargs)
        user.is_staff = user.is_superuser = True
        if commit:
            user.save()
        return user

    def get_by_natural_key(self, email):
        return self.get(email=email)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Base user model.
    """

    USERNAME_FIELD = "email"
    email = models.EmailField(
        _("E-mail"),
        db_index=True,
        unique=True,
        help_text=_(
            "Users can register additional e-mail addresses. This is the "
            "main e-mail address which is used for login."
        ),
    )
    name = models.CharField(
        _("Name"), max_length=140, help_text=_("Full name of the user.")
    )
    alias = models.CharField(
        _("Alias"),
        max_length=20,
        help_text=_("Public alias used to identify the user."),
    )
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into the admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = UserManager()

    # Properties defined for better compatibility with default user model
    username = property(lambda self: self.alias)
    first_name = property(lambda self: self.partition(" ")[0])
    last_name = property(lambda self: self.partition(" ")[-1])
    profile_class = None

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    @lazy
    def profile(self):
        profile_class = self.profile_class
        if profile_class is None:
            try:
                profile_class = apps.get_model(self._meta.app_label, "Profile")
            except KeyError:
                return None

        if self.id is None:
            return profile_class(user=self)
        else:
            try:
                return profile_class.objects.get(user=self)
            except ObjectDoesNotExist:
                return profile_class.objects.create(user=self)

    def save(self, *args, **kwargs):
        new = self.id is None
        if self.alias is None:
            self.alias = slugify(self.name)

        if new:
            with transaction.atomic():
                super().save(*args, **kwargs)
                if self.profile is not None:
                    self.profile.save()
        else:
            super().save(*args, **kwargs)

    def natural_key(self):
        return "email"

    def get_full_name(self):
        return self.name.strip()

    def get_short_name(self):
        return self.alias

    def get_absolute_url(self):
        return reverse("users:profile-detail", args=(self.id,))


class Profile(models.Model):
    """
    Social information about users.
    """

    user = models.OneToOneField(
        get_config("AUTH_USER_MODEL", "auth.User"),
        on_delete=models.CASCADE,
        verbose_name=_("user"),
        related_name="profile_ref",
    )

    # Delegates and properties
    username = delegate_to("user", read_only=True)
    name = delegate_to("user", read_only=True)
    first_name = delegate_to("user", read_only=True)
    last_name = delegate_to("user", read_only=True)
    alias = delegate_to("user", read_only=True)
    email = delegate_to("user", read_only=True)

    class Meta:
        abstract = True

    def __str__(self):
        if self.user is None:
            return __("Unbound profile")
        full_name = self.user.get_full_name() or self.user.username
        return __("%(name)s's profile") % {"name": full_name}

    def get_absolute_url(self):
        if self.user is not None:
            return self.user.get_absolute_url()
