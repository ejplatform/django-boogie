from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from boogie import models
from boogie.rest import rest_api
from .enums import Format


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


@rest_api(['full_path'])
class Path(models.Model):
    """
    Represent a path under which a file is saved.
    """

    parent = models.ForeignKey(
        'Path',
        blank=True, null=True,
        on_delete=models.CASCADE,
        related_name='children',
    )
    full_path = models.CharField(
        _('Full path'),
        max_length=300,
        unique=True,
    )

    class Meta:
        verbose_name = _('Path')
        verbose_name_plural = _('Paths')

    def __str__(self):
        return self.full_path

    def children(self, value):
        """
        Return a new child for the given path.
        """

    def paste(self, name, content):
        """
        Create a new paste with the given file name and content.
        """


@rest_api(['content', 'file_type'])
class Paste(TimeStampedModel):
    """
    Represents a single paste.
    """
    path = models.ForeignKey(
        'Path',
        on_delete=models.CASCADE,
        related_name='files',
    )
    file_name = models.NameField(
        _('File name'),
        validators=[check_valid_file_name],
    )
    file_type = models.EnumField(Format, _('File type'))
    content = models.TextField(_('Contents'))
    full_name = property(str)

    class Meta:
        unique_together = ('path', 'file_name')
        verbose_name = _('Paste')
        verbose_name_plural = _('Pastes')

    def __str__(self):
        return f'{self.path}{self.file_name}'


@rest_api.property(Paste)
def name(paste):
    return paste.full_name
