from collections import OrderedDict
from collections.abc import Sequence

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseBadRequest

from sidekick import lazy
from .route import Route, normalize_name, ModelLookupMixin, to_default_dict


# Django makes an instance check to see if urlpatterns is a list of path
# declarations. We inherit from list, but implement all methods using
# collections.Sequence. This is necessary since urls are only created after
# initialization of the Router.urls attribute.
class Router(ModelLookupMixin, Sequence, list):
    """
    A collection of routes.

    It exports a list of urlpatterns that can be included in a Django's url.py.
    """

    @lazy
    def urls(self):
        patterns = []
        pattern_groups = group_by_url(self.routes)
        for pattern, routes in pattern_groups.items():
            if len(routes) == 1:
                route, = routes
                patterns.append(route.path_handler(path_prefix=self.base_path))
            else:
                raise NotImplementedError(pattern)
        super().__setitem__(slice(None, None), patterns)
        return patterns

    cache = property(lambda self: self.extra_args["cache"])
    csrf = property(lambda self: self.extra_args["csrf"])
    decorators = property(lambda self: self.extra_args["decorators"])
    gzip = property(lambda self: self.extra_args["gzip"])
    login = property(lambda self: self.extra_args["login"])
    login_url = property(lambda self: self.extra_args["login_url"])
    missing_object_policy = property(
        lambda self: self.extra_args["missing_object_policy"]
    )
    perms = property(lambda self: self.extra_args["perms"])
    perms_policy = property(lambda self: self.extra_args["perms_policy"])
    xframe = property(lambda self: self.extra_args["xframe"])

    def __init__(
        self,
        base_name="",
        base_path="",
        template=None,
        models=None,
        lookup_field=None,
        lookup_type=None,
        **kwargs,
    ):
        list.__init__(self)
        ModelLookupMixin.__init__(self, models, lookup_field, lookup_type)
        self.routes = []
        self.base_name = base_name
        self.base_path = base_path
        self.template = template
        self.extra_args = kwargs

    def __call__(self, *args, **kwargs):
        return self.route(*args, **kwargs)

    def __len__(self):
        return len(self.urls)

    def __iter__(self):
        return iter(self.urls)

    def __getitem__(self, item):
        return self.urls[item]

    def route(self, path="", name=None, **kwargs):
        """
        Register a route from function. Users should provide a path and can
        provide any optional routing parameters.
        """

        def decorator(func):
            func.route = route = self.register(func, path, name, **kwargs)
            func.as_view = route.view_function
            return func

        return decorator

    def register(self, function, path="", name=None, template=None, **kwargs):
        """
        Register a function as a route.

        Similar to the .route method, but does not behave as a decorator.
        """

        # Use the last registered route if path is ellipsis
        if path is ... and not self.routes:
            msg = "cannot determine last url from empty router"
            raise ImproperlyConfigured(msg)
        elif path is ...:
            path = self.routes[-1].path

        # Check if should use the parent template or not
        name = normalize_name(name, function)
        if template is None and self.template is not None:
            if isinstance(self.template, str):
                template = self.template.format(name=name)
            else:
                template = [x.format(name=name) for x in self.template]
        kwargs["name"] = name
        kwargs["template"] = template

        # Check if it override any model and lookup fields and types
        models = dict(kwargs.get("models") or ())
        kwargs["models"] = dict(self.models, **models)
        update_lookup(self, kwargs, "lookup_field")
        update_lookup(self, kwargs, "lookup_type")

        # Create a Route object
        kwargs = dict(self.extra_args, **kwargs)
        route = Route(path, function, **kwargs)
        self.routes.append(route)

        # Save route to the list of registered routes
        try:
            routes = getattr(function, "routes", [])
            function.registered_routes = [*routes, route]
        except AttributeError:
            pass

        return route

    #
    # HTTP methods
    #
    def connect(self, *args, **kwargs):
        """
        Similar to :method:`route`, but sets the HTTP method to CONNECT.
        """
        return self.route(*args, method="CONNECT", **kwargs)

    def delete(self, *args, **kwargs):
        """
        Similar to :method:`route`, but sets the HTTP method to DELETE.
        """
        return self.route(*args, method="DELETE", **kwargs)

    def get(self, *args, **kwargs):
        """
        Similar to :method:`route`, but sets the HTTP method to GET.
        """
        return self.route(*args, method="GET", **kwargs)

    def head(self, *args, **kwargs):
        """
        Similar to :method:`route`, but sets the HTTP method to HEAD.
        """
        return self.route(*args, method="HEAD", **kwargs)

    def options(self, *args, **kwargs):
        """
        Similar to :method:`route`, but sets the HTTP method to OPTIONS.
        """
        return self.route(*args, method="OPTIONS", **kwargs)

    def patch(self, *args, **kwargs):
        """
        Similar to :method:`route`, but sets the HTTP method to PATCH.
        """
        return self.route(*args, method="PATCH", **kwargs)

    def post(self, *args, **kwargs):
        """
        Similar to :method:`route`, but sets the HTTP method to POST.
        """
        return self.route(*args, method="POST", **kwargs)

    def put(self, *args, **kwargs):
        """
        Similar to :method:`route`, but sets the HTTP method to PUT.
        """
        return self.route(*args, method="PUT", **kwargs)

    def trace(self, *args, **kwargs):
        """
        Similar to :method:`route`, but sets the HTTP method to TRACE.
        """
        return self.route(*args, method="TRACE", **kwargs)


def group_by_url(routes):
    dic = OrderedDict()
    for route in routes:
        paths = dic.setdefault(route.path, [])
        paths.append(route)
    return dic


def update_lookup(router, kwargs, field):
    original = getattr(router, field)
    new = kwargs.get(field, {})
    if isinstance(new, str):
        lookup = to_default_dict(new)
        lookup.update(original)
    else:
        lookup = original.copy()
        lookup.update(new)
    kwargs[field] = lookup


def multi_method_view(method_map):
    """
    Receives a mapping from HTTP method to view function and return a function
    dispatches to the correct implementation depending on the user requested
    method.
    """

    def view(request, **kwargs):
        try:
            handler = method_map[request.method]
        except KeyError:
            msg = f"method not allowed: {request.method}"
            return HttpResponseBadRequest(msg)
        return handler(request, **kwargs)

    return view
