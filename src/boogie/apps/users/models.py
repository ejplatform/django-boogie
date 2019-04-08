from django.apps import apps
from django.contrib.auth import models as auth
from django.utils.translation import ugettext_lazy as _
from sidekick import property as sk_property, placeholder as this

from boogie import models


class UserQuerySet(models.QuerySet):
    """
    Base queryset for Boogie users.
    """


class UserManager(auth.UserManager.from_queryset(UserQuerySet), models.Manager):
    """
    Base manager for Boogie users.
    """


class AbstractUser(auth.AbstractUser, models.Model):
    """
    A user object with a single name field instead of separate first_name and
    last_name.

    This is the abstract version of the model. Use it for subclassing.
    """

    name = models.CharField(
        _("Name"), max_length=255, default="", help_text=_("User's full name")
    )

    first_name = sk_property(this.name.partition(" ")[0])
    last_name = sk_property(this.name.partition(" ")[-1])

    @first_name.setter
    def first_name(self, value):
        pre, _, post = self.name.partition(" ")
        self.name = f"{value} {post}" if post else value

    @last_name.setter
    def last_name(self, value):
        pre, _, post = self.name.partition(" ")
        self.name = f"{pre} {value}" if post else value

    objects = UserManager()

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.name:
            self.name = self.username

    def __str__(self):
        return self.email


class User(AbstractUser):
    """
    Concrete version of Boogie's user model.
    """

    class Meta(auth.User.Meta):
        swappable = "AUTH_USER_MODEL"
        if not apps.is_installed("boogie.apps.users"):
            app_label = "boogie_users"
