import functools
import inspect
import re
from collections import defaultdict

import sidekick as sk
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
    user_passes_test,
)
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.shortcuts import render, redirect
from django.urls import path
from django.views.decorators.cache import never_cache, cache_control
from django.views.decorators.clickjacking import (
    xframe_options_exempt,
    xframe_options_deny,
    xframe_options_sameorigin,
)
from django.views.decorators.csrf import (
    csrf_exempt,
    ensure_csrf_cookie,
    requires_csrf_token,
    csrf_protect,
)
from django.views.decorators.gzip import gzip_page

from .paths import register_model_converter, get_lookup_type
from ..render import render_response


class Cte:
    def __init__(self, cte):
        self.value = cte

    def __call__(self, *args, **kwargs):
        return self.value

    def __repr__(self):
        return "Cte(%r)" % self.value


class ModelLookupMixin:
    """
    Common initialization patterns for Route and Router.
    """

    def __init__(self, models, lookup_field, lookup_type):
        # Normalize models
        self.models = dict(models or ())
        if isinstance(lookup_field, defaultdict):
            self.lookup_field = lookup_field.copy()
        else:
            self.lookup_field = to_default_dict(lookup_field or {}, "pk")
        if isinstance(lookup_type, defaultdict):
            self.lookup_type = lookup_type.copy()
        else:
            self.lookup_type = to_default_dict(lookup_type or {}, "str")


class Route(ModelLookupMixin):
    """
    A route is a combination of a Django view + some url pattern.
    """

    _default_redirect = staticmethod(
        user_passes_test(lambda x: False)(lambda request: None)
    )

    def __init__(
        self,
        path,
        func,
        name=None,
        method=None,
        template=None,
        login=False,
        perms=None,
        staff=False,
        cache=None,
        gzip=False,
        xframe=None,
        csrf=None,
        models=None,
        lookup_field="pk",
        lookup_type=None,
        decorators=(),
        login_url=None,
        perms_policy="default",
        missing_object_policy="default",
    ):
        super().__init__(models, lookup_field, lookup_type)
        self.path = path
        self.function = func
        self.name = normalize_name(name, func)
        self.method = method
        self.template = template
        self.login = login
        self.perms = perms
        self.staff = staff
        self.cache = cache
        self.gzip = gzip
        self.xframe = xframe
        self.csrf = csrf
        self.decorators = tuple(decorators)
        self.login_url = login_url
        self.perms_policy = perms_policy
        self.missing_object_policy = missing_object_policy

        if login or perms or staff:
            self._test_user = True
            self._register_perms(perms)
        else:
            self._test_user = False

    def _register_perms(self, perms):
        # Perms needs special handling: we only pass simple permissions that
        # do not involve access to some object when applying the decorator.
        # Complex perms must be handled inside the view function and cannot
        # use Django's standard @permission_required() mechanism.
        if isinstance(perms, str):
            perms = [perms]
        complex, simple = sk.partition_at(lambda x: ":" in x, perms or ())
        self._simple_perms = tuple(simple)

        # Create a tuple of (obj, [list of perms]) for
        complex_perms = []
        for full_perm in complex:
            perm, _, obj = full_perm.partition(":")

            # Check if any object permissions were defined inconsistently
            if obj not in self.models:
                raise ImproperlyConfigured(
                    f"invalid permission detected: {obj!r} object is required in \n"
                    f"{full_perm!r} permission, but it is not registered in this "
                    f"route."
                )
            complex_perms.append((perm, obj))

        self._complex_perms = tuple(complex_perms)

    def view_function(self):
        """
        Return a function that respects Django's view function contract.
        """

        function = as_request_function(self.function)
        decorators = ["cache", "gzip", "xframe", "csrf", "decorators"]
        kwargs = {attr: getattr(self, attr) for attr in decorators}

        # Creates the default view function.
        @apply_decorators(**kwargs)
        def view_function(request, **kwargs):
            try:
                self.prepare_arguments(request, kwargs)
                result = function(request, **kwargs)
                return self.prepare_response(result, request)
            except HttpExceptional as exc:
                return exc.get_response()

        return view_function

    def path_handler(self, prefix="", path_prefix=""):
        """
        Returns a django.urls.path (or re_path) object that handles the given
        route.
        """
        path_ = self.compatible_path(path_prefix)
        return path(path_, self.view_function(), name=prefix + self.name)

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

    def prepare_arguments(self, request, args):
        """
        Transforms the dictionary of input arguments inplace.

        This step transforms the view arguments before passing them to the view
        function.
        """
        models = self.models
        if self.missing_object_policy is not None:
            for arg, obj in args.items():
                if obj is None and arg in models:
                    self.handle_object_not_found(request)

        if self._test_user:
            user = request.user
            if (
                self.login
                and not user.is_authenticated
                or self.staff
                and not user.is_staff
                or not user.has_perms(self._simple_perms)
            ):
                self.handle_permission_denied(request)

            for perm, obj_name in self._complex_perms:
                obj = args[obj_name]
                if not user.has_perm(perm, obj):
                    self.handle_permission_denied(request)

    def compatible_path(self, path_prefix=""):
        """
        Convert a Boogie-style path specification to a valid Django path.
        """
        path = path_prefix + self.path

        for name, model in self.models.items():
            if isinstance(model, type) and issubclass(model, Model):
                queryset = None
            else:
                model, queryset = model.model, model

            part = f"<model:{name}>"
            if part in path:
                lookup_field = self.lookup_field[name]
                lookup_type = self.lookup_type[name]
                if lookup_type is None:
                    lookup_type = get_lookup_type(None, model, lookup_field)
                converter = get_converter(model, lookup_field, lookup_type, queryset)
                path = path.replace(part, f"<{converter}:{name}>")

        # Find unregistered models
        if "<model:" in path:
            m = re.search(r"<model:[^>]*>", path)
            part = path[m.start() : m.end()]
            name = part[7:-1]
            raise ImproperlyConfigured(
                f"Could not find a model for {part}. Please pass the correct "
                f"model for {name} in the models dictionary of the route."
            )
        return path

    def handle_object_not_found(self, request):
        """
        Decide what to do if object passed to some parameter of the view
        function is not found on the database.
        """
        policy = self.missing_object_policy
        if policy in ("default", 404):
            raise Http404
        elif policy in ("forbidden", 403):
            raise PermissionError
        elif policy in ("redirect", 302, 303):
            raise HttpExceptional(self._default_redirect(request))
        elif isinstance(policy, int):
            raise HttpExceptional(status_code=policy)
        else:
            raise ImproperlyConfigured("invalid policy")

    def handle_permission_denied(self, request):
        """
        Decide what to do if user does not have permission to see the page.
        """
        policy = self.perms_policy
        if policy in ("default", "redirect", 302, 303):
            raise HttpExceptional(self._default_redirect(request))
        elif policy in ("forbidden", 403):
            raise PermissionError
        elif policy in ("hide", 404):
            raise Http404
        elif isinstance(policy, int):
            raise HttpExceptional(status_code=policy)
        else:
            raise ImproperlyConfigured("invalid permission policy")


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

    if spec.args and spec.args[0] == "request":
        return function

    @functools.wraps(function)
    def request_function(request, *args, **kwargs):
        return function(*args, **kwargs)

    return request_function


def apply_decorators(  # noqa: C901
    view=None,
    login=False,
    staff=False,
    perms=None,
    cache=None,
    gzip=False,
    xframe=None,
    csrf=None,
    decorators=(),
):
    """
    Apply decorators to view function. Can also be used as a decorator.
    """

    if view is None:
        kwargs = locals()
        kwargs.pop("view")
        return lambda view: apply_decorators(view, **kwargs)

    # Cache control
    if cache is False:
        view = never_cache(view)
    elif cache is not None:
        view = cache_control(**cache)(view)

    # Permissions
    # (We keep the implementation here, but those options are not handled by
    #  this decorator anymore).
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
    elif xframe == "deny":
        view = xframe_options_deny(view)
    elif xframe == "sameorigin":
        view = xframe_options_sameorigin(view)
    if csrf is False:
        view = csrf_exempt(view)
    elif csrf == "cookie":
        view = ensure_csrf_cookie(view)
    elif csrf == "token":
        view = requires_csrf_token(view)
    elif csrf is True:
        view = csrf_protect(view)

    # Apply final decorators
    for decorator in reversed(decorators):
        view = decorator(view)
    return view


def staff_required(view):
    @functools.wraps(view)
    def decorated(request, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        return view(request, **kwargs)

    return decorated


def normalize_lookup(field, name=None):
    if isinstance(field, str):
        return field
    return field.get(name)


def normalize_name(name, function=None):
    if name:
        return name
    return function.__name__.replace("_", "-")


def to_default_dict(value, default=None):
    if isinstance(value, defaultdict):
        return value.copy()
    elif isinstance(value, dict):
        if default is not None:
            data = defaultdict(Cte(default))
            data.update(value)
            return data
        else:
            return dict(value)
    else:
        return defaultdict(Cte(value))


@functools.lru_cache(maxsize=256)
def get_converter(model, lookup_field, lookup_type, queryset):
    if queryset is None:
        name = f"${model.__name__}.{lookup_field}-{lookup_type}"
    else:
        name = f"${model.__name__}.{lookup_field}-{lookup_type}-{id(queryset)}"
    register_model_converter(model, name, lookup_field, lookup_type, queryset)
    return name


#
# Exceptional handling of events
#
class HttpExceptional(Exception):
    """
    Exception raised
    """

    def __init__(self, msg=None, status_code=500, cls=HttpResponse, **kwargs):
        super().__init__(msg, status_code, cls, kwargs)

    def get_response(self):
        msg, status_code, cls, kwargs = self.args
        if isinstance(msg, HttpResponse):
            return msg
        return cls(msg, status=status_code, **kwargs)


class HttpRedirect(HttpExceptional):
    def __init__(self, to, **kwargs):
        super(Exception, self).__init__(to, kwargs)

    def get_response(self):
        to, kwargs = self.args
        return redirect(to, **kwargs)
