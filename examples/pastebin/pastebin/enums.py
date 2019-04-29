from django.utils.translation import ugettext_lazy as _

from boogie.fields import Enum

EXTENSION_MAP = {}
TYPE_MAP = {}


class Format(Enum):
    """
    File type format.
    """

    @classmethod
    def from_extension(cls, ext):
        """
        Compute format field from extension.

        >>> Format.from_extension('py')
        Format.PYTHON
        """
        return EXTENSION_MAP.get(ext, cls.TEXT)

    @classmethod
    def from_filename(cls, name):
        """
        Compute format field from file name.

        >>> Format.from_filename('foo.py')
        Format.PYTHON
        """
        _, _, ext = name.rpartition('.')
        return cls.from_extension(ext)

    TEXT = 'txt', _('Plain text')
    PYTHON = 'py', _('Python')
    HTML = 'html', _('HTML')
    JAVASCRIPT = 'js', _('Javascript')


TYPE_MAP.update({
    Format.TEXT: ['txt'],
    Format.PYTHON: ['py'],
    Format.HTML: ['html', 'htm'],
})


EXTENSION_MAP.update(
    (ext, kind) for kind, exts in TYPE_MAP.items() for ext in exts
)
