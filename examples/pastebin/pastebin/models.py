from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from boogie import models
from boogie.rest import rest_api
from .enums import Format
from .validators import check_valid_file_name


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
    name = models.CharField(
        _('Full path'),
        max_length=300,
        unique=True,
    )

    class Meta:
        verbose_name = _('Path')
        verbose_name_plural = _('Paths')

    def __str__(self):
        return self.name

    def child(self, name: str):
        """
        Return a new child for the given path.
        """
        path = f'{self.name}{name}/'
        obj, _ = Path.objects.get_or_create(parent=self, name=path)
        return obj

    def paste(self, name, content, *, commit=True, **kwargs):
        """
        Create a new paste with the given file name and content.
        """
        paste = Paste(parent=self, name=name, content=content, **kwargs)
        if commit:
            paste.save()
        return paste


@rest_api(['path', 'content', 'content_type'])
class Paste(TimeStampedModel):
    """
    Represents a single paste.
    """
    parent = models.ForeignKey(
        'Path',
        on_delete=models.CASCADE,
        related_name='files',
    )
    name = models.NameField(
        _('File name'),
        validators=[check_valid_file_name],
    )
    content_type = models.EnumField(Format, _('Content type'))
    content = models.TextField(_('Source code'))
    email = models.EmailField(_('Recovery e-mail'), blank=True)
    password = models.CharField(_('Password'), blank=True, max_length=256)
    path = property(str)

    class Meta:
        unique_together = ('parent', 'file_name')
        verbose_name = _('Paste')
        verbose_name_plural = _('Pastes')

    def __str__(self):
        return f'{self.parent}{self.file_name}'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.content_type:
            self.content_type = content_type(self.name)


def path(name: str):
    """
    Return a path object for the given path.
    """

    if name in ('/', ''):
        return Path.objects.get_or_create('/')[0]
    name.rstrip('/').lstrip('/')

    try:
        return Path.objects.get(f'/{name}/')
    except Path.DoesNotExist:
        base, _, last = name.rpartition('/')
        return path(base.rstrip()).child(last)


def paste(path, content, **kwargs):
    """
    Create a new paste object under the given path.
    """

    path, _, name = path.rpartition('/')
    path = path(path)
    return path.paste(name, content, **kwargs)


def content_type(name):
    """
    Derive content type from extension.
    """
    return Python
