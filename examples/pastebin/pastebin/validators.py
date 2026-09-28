from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


def check_valid_file_name(name):
    if '/' in name:
        raise ValidationError(_(f'invalid file name: {name}'))
    if not name:
        raise ValidationError(_('Empty name'))


def check_valid_path(name):
    if not name.endswith('/'):
        raise ValidationError(_(f'path must end with an /'))
    if not name.startswith('/'):
        raise ValidationError(_(f'path must start with an /'))