from boogie import models
from django.utils.translation import ugettext_lazy as _

from .validators import validate_color


class Color(models.Model):
    """
    Generic color reference that can be configured in the admin interface.
    """

    name = models.CharField(_("Color name"), max_length=150)
    hex_value = models.CharField(
        _("Color"),
        max_length=30,
        help_text=_("Color code in hex (e.g., #RRGGBBAA) format."),
        validators=[validate_color],
    )

    def __str__(self):
        return f"{self.name}: {self.hex_value}"

    def __html__(self):
        return self.hex_value
