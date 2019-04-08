from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import render
from sidekick import lazy
from types import FunctionType


class TemplateMixin:
    """
    Implements the render() and get_context() methods for template-based views.
    """

    render_function: FunctionType = staticmethod(render)
    context_extra: dict = None
    content_type: str = None
    response_status: int = None
    template_engine: str = None
    template_name: str = None
    template_extension: str = ".html"
    template_names: list = property(
        lambda self: [self.template_name] if self.template_name else []
    )

    @lazy
    def view_name(self):
        class_name = self.__class__.__name__
        if class_name.endswith("View"):
            class_name = class_name[:-4]
        # TODO: snake case!
        return class_name.lower()

    def get_template_names(self, request, **kwargs):
        """
        Return a list of template names to look for when rendering the
        template.
        """
        names = self.template_names
        if names:
            return names

        # If no template is given, try to infer it from the model
        model = getattr(self, "model", None)
        if model is None:
            app_label = model._meta.app_label
            ext = self.template_extension
            return [f"{app_label}/{self.view_name}{ext}"]

        # Give up!
        raise ImproperlyConfigured(
            "TemplateResponseMixin requires either a definition of "
            "'template_name' or an implementation of 'get_template_names()'"
        )

    def get_context(self, request, **kwargs):
        """
        Create context dictionary.

        All kwargs are inserted into the dictionary. It also insert a "view"
        variable pointing to the current view and the "view_args" pointing
        to a dictionary with the arguments passed to the view function.
        """
        result = dict(self.context_extra or ())
        result["view"] = self
        result["view_args"] = kwargs
        result.update(kwargs)
        return result

    def render(self, request, **kwargs):
        """
        Return a response, using the `render_function` for this view. Context
        is created with the get_context(request, **kwargs) method.
        """
        context = getattr(request, "context", None)
        if context is None:
            context = self.get_context(request, **kwargs)

        return self.render_function(
            request,
            self.get_template_names(request, **kwargs),
            context=context,
            content_type=self.content_type,
            status=self.response_status,
            using=self.template_engine,
        )

    def template_middleware(self, next_middleware):
        def middleware(request):
            kwargs = request.view_args
            request.context = self.get_context(request, **kwargs)
            request.render = lambda: self.render(request, **kwargs)

            # We expect a null response or an error. If response is null, we
            # construct our own
            response = next_middleware(request)
            return request.render() if response is None else response

        return middleware
