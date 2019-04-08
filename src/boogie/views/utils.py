import functools

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed, ImproperlyConfigured
from django.core.handlers.exception import (
    get_exception_response,
    response_for_exception,
)
from django.urls import get_resolver, get_urlconf
from django.utils.module_loading import import_string

from boogie.views.base import log
from .middleware import BOOGIE_VIEW_MIDDLEWARES


def not_implemented(request, **kwargs):
    raise NotImplementedError


def allowed_methods(view):
    """
    Return the default list of allowed HTTP methods for the view.
    """
    cls = type(view)
    all_methods = ["get", "post", "delete", "put"]
    implemented = (
        attr for attr in all_methods if getattr(cls, attr) is not not_implemented
    )
    return ["options", *implemented]


def method_map(view):
    """
    Return a dictionary mapping HTTP method names to their corresponding
    view functions.
    """
    wrapper = view.wrap_method
    return dict(
        GET=wrapper(getattr(view, "get", not_implemented)),
        POST=wrapper(getattr(view, "post", not_implemented)),
        DELETE=wrapper(getattr(view, "delete", not_implemented)),
        PUT=wrapper(getattr(view, "put", not_implemented)),
        OPTIONS=wrapper(getattr(view, "options", not_implemented)),
    )


def middleware_chain(middleware_list, handler):
    """
    Reduces the middleware chain into a single handler.
    """

    handler = safe_handler(handler)

    for ref in middleware_list:
        factory = load_middleware(ref)
        try:
            middleware = factory(handler)
        except MiddlewareNotUsed as exc:
            if settings.DEBUG:
                log.debug(f"MiddlewareNotUsed({exc}): {ref}")
            continue
        handler = safe_handler(middleware)

    return handler


def safe_handler(get_response):
    @functools.wraps(get_response)
    def inner(request):
        try:
            response = get_response(request)
        except TimeoutError as exc:
            log.warning(
                f"Timeout: {request.path}",
                extra={"status_code": 408, "request": request},
            )
            resolver = get_resolver(get_urlconf())
            response = get_exception_response(request, resolver, 408, exc)
        except Exception as exc:
            response = response_for_exception(request, exc)
        return response

    return inner


def load_middleware(ref):
    """
    Loads a middleware from a string reference. Callable objects are just
    pass-thru.
    """

    if callable(ref):
        return ref
    elif not isinstance(ref, str):
        raise TypeError(f"invalid middleware reference: {ref.__class__}")
    if "." in ref:
        return import_string(ref)
    try:
        return BOOGIE_VIEW_MIDDLEWARES[ref]
    except KeyError:
        raise ImproperlyConfigured(
            f"There is no middleware registered as {ref}. You can register, "
            f"new boogie view middlewares in the BOOGIE_VIEW_MIDDLEWARES "
            f"setting in the settings module."
        )
