import functools
import inspect

from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.urls import path
from django.views.decorators.cache import never_cache, cache_control
from django.views.decorators.clickjacking import xframe_options_exempt, xframe_options_deny, xframe_options_sameorigin
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie, requires_csrf_token, csrf_protect
from django.views.decorators.gzip import gzip_page

from boogie.render import render_response


class Route:
    """
    A route is a combination of a Django view + some url pattern.
    """

    def __init__(self, path, func, name=None, method=None, template=None,
                 login=False, perms=None, staff=False,
                 cache=None, gzip=False, xframe=None, csrf=None,
                 decorators=()):
        self.path = path
        self.function = func
        self.name = name
        self.method = method
        self.template = template
        self.login = login
        self.perms = perms
        self.staff = staff
        self.cache = cache
        self.gzip = gzip
        self.xframe = xframe
        self.csrf = csrf
        self.decorators = decorators

        if name is None:
            self.name = func.__name__.replace('_', '-')

    def view_function(self):
        """
        Return a function that respects Django's view function contract.
        """

        function = as_request_function(self.function)
        decorators = ['login', 'perms', 'cache', 'gzip', 'xframe', 'csrf']
        kwargs = {attr: getattr(self, attr) for attr in decorators}

        @apply_decorators(**kwargs)
        def view_function(request, **kwargs):
            result = function(request, **kwargs)
            return self.prepare_response(result, request)

        return view_function

    def path_handler(self, prefix=''):
        """
        Returns a django.urls.path (or re_path) object that handles the given
        route.
        """
        return path(self.path, self.view_function(), name=prefix + self.name)

    def prepare_response(self, result, request):
        """
        Return a Django response object from the result of the supplied view
        function.
        """
        # Regular http responses
        if isinstance(result, HttpResponse):
            return result

        # Template context
        elif isinstance(result, dict) and self.template is not None:
            return render(request, self.template, result)

        # Other types
        return render_response(result)


#
# Auxiliary functions
#
def as_request_function(function):
    """
    Inspect to check if function receives a request as first parameter and
    return either the original function (if it expects a request) or a
    transformed function that omits the first parameter.
    """
    spec = inspect.getfullargspec(function)

    if spec.args and spec.args[0] == 'request':
        return function
    return lambda request, *args, **kwargs: function(*args, **kwargs)


def apply_decorators(view=None, login=False, staff=False, perms=None,  # noqa: C901
                     cache=None, gzip=False, xframe=None, csrf=None,
                     decorators=()):
    """
    Apply decorators to view function. Can also be used as a decorator.
    """

    if view is None:
        kwargs = locals()
        kwargs.pop('view')
        return lambda view: apply_decorators(view, **kwargs)

    # Cache control
    if cache is False:
        view = never_cache(view)
    elif cache is not None:
        view = cache_control(**cache)(view)

    # Permissions
    if login:
        view = login_required(view)
    if perms:
        view = permission_required(perms)(view)
    if staff:
        view = staff_required(view)

    # Compression
    if gzip:
        view = gzip_page(view)

    # Security
    if xframe is False:
        view = xframe_options_exempt(view)
    elif xframe == 'deny':
        view = xframe_options_deny(view)
    elif xframe == 'sameorigin':
        view = xframe_options_sameorigin(view)
    if csrf is False:
        view = csrf_exempt(view)
    elif csrf == 'cookie':
        view = ensure_csrf_cookie(view)
    elif csrf == 'token':
        view = requires_csrf_token(view)
    elif csrf is True:
        view = csrf_protect(view)

    # Apply final decorators
    for decorator in decorators:
        view = decorator(view)
    return view


def staff_required(view):
    @functools.wraps(view)
    def decorated(request, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        return view(request, **kwargs)

    return decorated
