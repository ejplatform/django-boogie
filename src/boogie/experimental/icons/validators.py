from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from hyperpython.components.fa_icons import COLLECTIONS


def validate_icon_name(icon_name):
    if icon_name not in COLLECTIONS:
        raise ValidationError(
            _(
                "Invalid font awesome icon name. Please use the short format (i.e., "
                '"facebook-f" instead of "fab fa-facebook-f"'
            )
        )


def default_icon_name(social):
    """
    Return icon from the given social network
    """
    try:
        return SOCIAL_ICONS[social.lower()]
    except KeyError:
        raise ValueError(f"unknown social network: {social}")


SOCIAL_ICONS = {
    **{
        net: net
        for net in (
            "bitbucket facebook github instagram medium pinterest telegram "
            "tumblr twitter whatsapp".split()
        )
    },
    **{
        "google plus": "google-plus-g",
        "google+": "google-plus-g",
        "reddit": "redit-alien",
        "stack overflow": "stackoverflow",
    },
}
