import logging

from django.http import HttpResponse

from .utils import not_implemented, allowed_methods, method_map, middleware_chain

log = logging.getLogger("django.request")


class View:
    """
    Boogie class-based views.
    """

    # Default attributes
    template_name = None
    allowed_methods = None
    middleware = ()

    def __init__(self, *, middlewares=(), **kwargs):
        # Init keyword arguments
        cls = type(self)
        for k, v in kwargs.items():
            if hasattr(cls, k):
                setattr(self, k, v)
            else:
                raise TypeError(f"{k} is not an attribute of {cls.__name}")

        self._method_map = method_map(self)
        if self.allowed_methods is None:
            self.allowed_methods = allowed_methods(self)

        self.middlewares = self.select_middlewares(middlewares)
        self._middleware_chain = middleware_chain(
            self.middlewares, self.request_handler
        )

    def __call__(self, request, **kwargs):
        return self.respond(request, **kwargs)

    def wrap_method(self, method):
        """
        Prepare a method to respect the view function contract.
        """
        return method

    def select_middlewares(self, middlewares):
        """
        May inject additional middlewares depending on the features requested
        by the view function.
        """
        return middlewares

    def respond(self, request, **kwargs):
        """
        Respond to request.

            view.respond(request, **kwargs) <==> view(request, **kwargs)
        """
        request.view = self
        request.view_args = kwargs
        return self._middleware_chain(request)

    def request_handler(self, request):
        """
        Last point of the middleware chain: receive a request and return a
        response.
        """
        handler = self._method_map[request.method]
        return handler(request, **request.view_args)

    #
    # Http methods
    #
    get = post = delete = put = not_implemented

    def options(self, request, *args, **kwargs):
        """
        Handle responding to requests for the OPTIONS HTTP verb.
        """
        response = HttpResponse()
        methods = map(str.upper, self.allowed_methods)
        response["Allow"] = ", ".join(methods)
        response["Content-Length"] = "0"
        return response
