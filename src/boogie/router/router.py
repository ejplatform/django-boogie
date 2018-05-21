from collections import OrderedDict

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseBadRequest

from sidekick import lazy
from .route import Route


class Router:
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
                patterns.append(route.path_handler())
            else:
                raise NotImplementedError
        return patterns

    def __init__(self):
        self.routes = []

    def __call__(self, *args, **kwargs):
        return self.route(*args, **kwargs)

    def __len__(self):
        return len(self.urls)

    def __iter__(self):
        return iter(self.urls)

    def __getitem__(self, item):
        return self.urls[item]

    def route(self, path='', **kwargs):
        """
        Register a route from function. Users should provide a path and can
        provide any optional routing parameters.
        """

        def decorator(func):
            self.register(func, path, **kwargs)
            return func

        return decorator

    def register(self, function, path='', **kwargs):
        """
        Register a function as a route.

        Similar to the .route method, but does not behave as a decorator.
        """
        if path is ... and not self.routes:
            msg = 'cannot determine last url from empty router'
            raise ImproperlyConfigured(msg)
        elif path is ...:
            path = self.routes[-1].path

        route = Route(path, function, **kwargs)
        self.routes.append(route)

        try:
            routes = getattr(function, 'routes', [])
            function.registered_routes = [*routes, route]
        except AttributeError:
            pass

    #
    # HTTP methods
    #
    def connect(self, *args, **kwargs):
        """
        Similar to :method:`route`, but sets the HTTP method to CONNECT.
        """
        return self.route(*args, method='CONNECT', **kwargs)

    def delete(self, *args, **kwargs):
        """
        Similar to :method:`route`, but sets the HTTP method to DELETE.
        """
        return self.route(*args, method='DELETE', **kwargs)

    def get(self, *args, **kwargs):
        """
        Similar to :method:`route`, but sets the HTTP method to GET.
        """
        return self.route(*args, method='GET', **kwargs)

    def head(self, *args, **kwargs):
        """
        Similar to :method:`route`, but sets the HTTP method to HEAD.
        """
        return self.route(*args, method='HEAD', **kwargs)

    def options(self, *args, **kwargs):
        """
        Similar to :method:`route`, but sets the HTTP method to OPTIONS.
        """
        return self.route(*args, method='OPTIONS', **kwargs)

    def patch(self, *args, **kwargs):
        """
        Similar to :method:`route`, but sets the HTTP method to PATCH.
        """
        return self.route(*args, method='PATCH', **kwargs)

    def post(self, *args, **kwargs):
        """
        Similar to :method:`route`, but sets the HTTP method to POST.
        """
        return self.route(*args, method='POST', **kwargs)

    def put(self, *args, **kwargs):
        """
        Similar to :method:`route`, but sets the HTTP method to PUT.
        """
        return self.route(*args, method='PUT', **kwargs)

    def trace(self, *args, **kwargs):
        """
        Similar to :method:`route`, but sets the HTTP method to TRACE.
        """
        return self.route(*args, method='TRACE', **kwargs)


def group_by_url(routes):
    dic = OrderedDict()
    for route in routes:
        paths = dic.setdefault(route.path, [])
        paths.append(route)
    return dic


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
            msg = f'method not allowed: {request.method}'
            return HttpResponseBadRequest(msg)
        return handler(request, **kwargs)

    return view
