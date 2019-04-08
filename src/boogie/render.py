import html
import io
from functools import singledispatch

from django.conf import settings
from django.http import HttpResponseServerError, HttpResponse


@singledispatch
def render_response(obj):
    """
    Convert arbitrary Python objects to http responses.

    By default, it tries to render object using :func:`render_html`. If it
    cannot be rendered that way and no handler was specified for the object
    type, it returns a :class:`django.http.HttpResponseServerError` response.
    """
    try:
        html = render_html(obj)
    except TypeError:
        if settings.DEBUG:
            msg = f"bad result from a view function: {repr(obj)}"
            return HttpResponseServerError(msg)
        else:
            return HttpResponseServerError()
    else:
        return HttpResponse(html)


@render_response.register(str)
def _(st):
    return HttpResponse(html.escape(st))


def render_html(obj):
    """
    Renders object as an HTML string in the given file.

    The function should write to the
    """
    handler = dump_html.dispatch(type(obj))
    file = io.StringIO()
    handler(obj, file)
    return file.getvalue()


@singledispatch
def dump_html(obj, file):
    """
    Write HTML representation of object in the given file handler.
    """
    type_name = obj.__class__.__name__
    raise TypeError(f"cannot convert {type_name} to html")


#
# Register hyperpython, if available
#
try:
    from hyperpython import Element, Text
except ImportError:
    pass
else:

    @dump_html.register(Element)
    @dump_html.register(Text)
    def _(x, fd):
        x.dump(fd)

    @render_response.register(Element)
    @render_response.register(Text)
    def _(x):
        return HttpResponse(str(x))
