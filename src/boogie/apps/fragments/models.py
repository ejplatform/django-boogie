from django.utils.translation import ugettext_lazy as _

from boogie import models
from boogie.fields import EnumField
from . import invalidate_cache
from .enums import Format


class Fragment(models.Model):
    """
    Configurable HTML fragments that can be inserted in pages.
    """

    ref = models.CharField(
        _("Identifier"),
        max_length=100,
        unique=True,
        db_index=True,
        help_text=_("Unique identifier for fragment name"),
    )
    title = models.CharField(
        max_length=100,
        blank=True,
        help_text=_(
            "Optional description that helps humans identify the content and "
            "role of the fragment."
        ),
    )
    format = EnumField(
        Format, _("Format"), help_text=_("Defines how content is interpreted.")
    )
    content = models.TextField(
        _("content"),
        blank=True,
        help_text=_("Raw fragment content in HTML or Markdown"),
    )
    editable = models.BooleanField(default=True, editable=False)

    def __str__(self):
        return self.ref

    def __html__(self):
        return str(self.render())

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        invalidate_cache(self.ref)

    def delete(self, using=None, keep_parents=False):
        super().delete(using, keep_parents)
        invalidate_cache(self.ref)

    def lock(self):
        """
        Prevents fragment from being deleted on the admin.
        """
        FragmentLock.objects.update_or_create(fragment=self)

    def unlock(self):
        """
        Allows fragment being deleted.
        """
        FragmentLock.objects.filter(fragment=self).delete()

    def render(self, request=None, **kwargs):
        """Render element to HTML"""
        return self.format.render(self.content, request, kwargs)


class FragmentLock(models.Model):
    """
    ForeignKey reference that prevents protected fragments from being deleted
    from the database.
    """

    fragment = models.OneToOneField(
        Fragment, on_delete=models.PROTECT, related_name="lock_ref"
    )
