# from django.urls import path


class Router:
    """
    A collection of routes.

    It exports a list of urlpatterns that can be included in a Django's url.py.
    """

    @property
    def patterns(self):
        return []

    def __init__(self):
        self._routes = []
        self._last_url = None

    def __call__(self, url, *args, **kwargs):
        if url is ...:
            url = self._last_url
        self._last_url = url
        append_route = self._routes.append

        if args:
            view_function, = args
            route = Route(url, view_function, **kwargs)
            append_route(route)
            return route
        else:
            # Decorator form
            return lambda view: append_route(Route(url, view)) or view

    #
    # HTTP methods
    #
    def connect(self, *args, **kwargs):
        return self(*args, method='CONNECT', **kwargs)

    def delete(self, *args, **kwargs):
        return self(*args, method='DELETE', **kwargs)

    def get(self, *args, **kwargs):
        return self(*args, method='GET', **kwargs)

    def head(self, *args, **kwargs):
        return self(*args, method='HEAD', **kwargs)

    def options(self, *args, **kwargs):
        return self(*args, method='OPTIONS', **kwargs)

    def patch(self, *args, **kwargs):
        return self(*args, method='PATCH', **kwargs)

    def post(self, *args, **kwargs):
        return self(*args, method='POST', **kwargs)

    def put(self, *args, **kwargs):
        return self(*args, method='PUT', **kwargs)

    def trace(self, *args, **kwargs):
        return self(*args, method='TRACE', **kwargs)


class Route:
    """
    Represents a Boogie route.
    """

    def __init__(self, path, function, name=None, template=None, login=False, perms=None, method=None):
        self.path = as_path(path)
        self.function = function
        self.name = name
        self.template = template
        self.login = login
        self.perms = perms
        self.method = method


class Path:
    """
    A path that uses an extended Django path.
    """

    def __init__(self, path):
        self.string = path


def as_path(path):
    return path if isinstance(path, Path) else Path(path)
