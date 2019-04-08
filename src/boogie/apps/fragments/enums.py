from functools import lru_cache

from django.template import engines
from django.utils.translation import ugettext_lazy as _
from hyperpython import Text, Blob
from hyperpython.components import markdown
from sidekick import import_later

from boogie.fields import IntEnum

bleach = import_later("bleach")
django_template = import_later("django.template.backends.django")
jinja2_template = import_later("django.template.backends.jinja2")

RENDERER = {}
renderer = lambda fmt: lambda f: RENDERER.setdefault(fmt, f)


class Format(IntEnum):
    """
    Data format.
    """

    TEXT = 0, _("Text")
    HTML_RAW = 1, _("HTML")
    HTML_TRUSTED = 2, _("Trusted (non-sanitized) HTML data.")
    MARKDOWN = 10, _("Markdown content")
    DJANGO_TEMPLATE = 20, _("A Django template")
    JINJA_TEMPLATE = 21, _("A Jinja template")

    def render(self, data, request, ctx):
        """
        Render a string of text as the given format.
        """
        return RENDERER[self](data, request, ctx)


@renderer(Format.TEXT)
def _(data, request, ctx):
    return Text(data)


@renderer(Format.HTML_RAW)
def _(data, request, ctx):
    return Blob(sanitize_html(data))


@renderer(Format.HTML_TRUSTED)
def _(data, request, ctx):
    return Blob(data)


@renderer(Format.MARKDOWN)
def _(data, request, ctx):
    return markdown(data)


@renderer(Format.DJANGO_TEMPLATE)
def _(data, request, ctx):
    return render_template("django", data, request, ctx)


@renderer(Format.JINJA_TEMPLATE)
def _(data, request, ctx):
    return render_template("jinja2", data, request, ctx)


#
# Auxiliary functions
#
def sanitize_html(html):
    """
    Convert a string of user HTML in safe html.
    """
    return bleach.clean(html, tags=TAG_WHITELIST, attributes=ATTR_WHITELIST)


def render_template(kind, data, request, ctx):
    template = get_template(data, kind)
    rendered = template.render(ctx, request=request)
    return Text(rendered, escape=False)


@lru_cache(1024)
def get_template(data, fmt):
    engine = engines[fmt]

    if fmt == "django":
        return django_template.Template(data, engine)
    elif fmt == "jinja2":
        return jinja2_template.Template(data, engine)
    else:
        raise ValueError(f"invalid template name: {fmt}")


#
# Constants
#

# List of valid tags to pass through the sanitizer
TAG_WHITELIST = bleach.ALLOWED_TAGS + [
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6" "img",
    "div",
    "span",
    "p",
]

# Valid attributes in each tag
ATTR_WHITELIST = bleach.ALLOWED_ATTRIBUTES
