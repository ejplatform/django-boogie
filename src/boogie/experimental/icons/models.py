from boogie import models
from django.utils.translation import ugettext_lazy as _
from hyperpython import a
from hyperpython.components import fa_icon
from hyperpython.components.icons import FA_COLLECTIONS

from .validators import validate_icon_name, default_icon_name


class SocialIcon(models.Model):
    """
    Configurable reference to a social media icon.
    """

    social_network = models.CharField(
        _("Social network"),
        max_length=50,
        unique=True,
        help_text=_("Name of the social network (e.g., Facebook)"),
    )
    icon_name = models.CharField(
        _("Icon name"),
        max_length=50,
        help_text=_(
            "Icon name in font-awesome. Use short version like "
            '"google", "facebook-f", etc.'
        ),
        validators=[validate_icon_name],
    )
    index = models.PositiveSmallIntegerField(
        _("Ordering"),
        default=0,
        help_text=_(
            "You can manually define the ordering that each icon should "
            "appear in the interface. Otherwise, icons will be shown in "
            "insertion order."
        ),
    )
    url = models.URLField(_("URL"), help_text=_("Link to your social account page."))

    @property
    def fa_class(self):
        collection = FA_COLLECTIONS.get(self.icon_name)
        return collection and f"{collection} fa-{self.icon_name}"

    class Meta:
        ordering = ["index", "id"]
        verbose_name = _("Social media icon")
        verbose_name_plural = _("Social media icons")

    def __str__(self):
        return self.social_network

    def __html__(self):
        if self.url:
            return str(self.link_tag())
        else:
            return str(self.icon_tag())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fill_social_icon()

    def _fill_social_icon(self):
        if not self.icon_name:
            self.icon_name = default_icon_name(self.social_network.casefold())

    def icon_tag(self, classes=()):
        """
        Render an icon tag for the given icon.

        >>> print(icon.icon_tag(classes=['header-icon']))       # doctest: +SKIP
        <i class="fa fa-icon header-icon"></i>
        """
        return fa_icon(self.icon_name, class_=classes)

    def link_tag(self, classes=(), icon_classes=()):
        """
        Render an anchor tag with the link for the social network.

        >>> print(icon.link_tag(classes=['header-icon']))       # doctest: +SKIP
        <a href="url"><i class="fa fa-icon header-icon"></i></a>
        """
        return a(href=self.url, class_=classes)[self.icon_tag(icon_classes)]
