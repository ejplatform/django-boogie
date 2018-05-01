import logging

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.http import HttpResponse, HttpResponsePermanentRedirect, HttpResponseRedirect, HttpResponseGone, Http404
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import ugettext as _
from lazyutils import lazy

log = logging.getLogger('django.request')


class TemplateMixin:
    """
    Implements the render() and get_context() methods for template-based views.
    """
    render_function = render
    context_extra = None
    content_type = None
    response_status = None
    template_engine = None
    template_name = None
    template_extension = '.html'
    template_names = property(
        lambda self: [self.template_name] if self.template_name else []
    )

    @lazy
    def view_name(self):
        class_name = self.__class__.__name__
        if class_name.endswith('View'):
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
        model = getattr(self, 'model', None)
        if model is None:
            app_label = model._meta.app_label
            ext = self.template_extension
            return [f'{app_label}/{self.view_name}{ext}']

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
        result['view'] = self
        result['view_args'] = kwargs
        result.update(kwargs)
        return result

    def render(self, request, **kwargs):
        """
        Return a response, using the `render_function` for this view. Context
        is created with the get_context(request, **kwargs) method.
        """
        context = getattr(request, 'context', None)
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


class View:
    """
    A reinterpretation of class-based views.
    """
    # Default attributes
    template_name = None
    middleware = ()

    def __init__(self, **kwargs):
        cls = type(self)
        for k, v in kwargs.items():
            if hasattr(cls, k):
                setattr(self, k, v)
            else:
                raise TypeError(f'{k} is not an attribute of {cls.__name}')
        self._method_map = dict(
            GET=self.get,
            POST=self.post,
            DELETE=self.delete,
            PUT=self.put,
        )

    def __call__(self, request, **kwargs):
        return self.handle(request, **kwargs)

    def handle(self, request, **kwargs):
        request.view_args = kwargs
        handler = self._method_map[request.method]

        if self.middleware:
            return run_middleware(self.middleware, handler)(request)
        else:
            return handler(request, **kwargs)

    # Http methods
    def allowed_methods(self, request, **kwargs):
        pass

    def get(self, request, **kwargs):
        raise NotImplementedError

    def post(self, request, **kwargs):
        raise NotImplementedError

    def delete(self, request, **kwargs):
        raise NotImplementedError

    def put(self, request, **kwargs):
        raise NotImplementedError

    def options(self, request, *args, **kwargs):
        """Handle responding to requests for the OPTIONS HTTP verb."""
        response = HttpResponse()
        response['Allow'] = ', '.join(self._allowed_methods())
        response['Content-Length'] = '0'
        return response

    # Middlewares
    def authentication(self, request):
        response = yield request
        yield response

    # Utility methods
    def get_object(self, request, **kwargs):
        return ImproperlyConfigured(
            'sdfsd'
        )


def run_middleware(middleware, handler):
    middleware = list(middleware)
    for factory in middleware:
        handler = factory(handler)
    return handler


def convert_to_middleware(method):
    def factory(get_response):
        def middleware(request):
            iterator = method(request)
            iterator.send(None)
            response = get_response(request)
            return iterator.send(response)

        return middleware

    return factory


class RedirectView(View):
    """
    Provide a redirect on any GET request.
    """

    permanent = False
    url = None
    pattern_name = None
    query_string = False

    def get_redirect_url(self, request, **kwargs):
        """
        Return the URL redirect to. Keyword arguments from the URL pattern
        match generating the redirect request are provided as kwargs to this
        method.
        """
        if self.url:
            url = self.url.format(**kwargs)
        elif self.pattern_name:
            url = reverse(self.pattern_name, kwargs=kwargs)
        else:
            return None

        query_args = request.META.get('QUERY_STRING', '')
        if query_args and self.query_string:
            url = f'{url}?{query_args}'
        return url

    def get(self, request, *args, **kwargs):
        url = self.get_redirect_url(*args, **kwargs)
        if url:
            if self.permanent:
                return HttpResponsePermanentRedirect(url)
            else:
                return HttpResponseRedirect(url)
        else:
            log.warning(
                'Gone: %s', request.path,
                extra={'status_code': 410, 'request': request}
            )
            return HttpResponseGone()

    head = post = options = delete = put = patch = get


class DetailView(TemplateMixin, View):
    """
    Provide the ability to retrieve a single object for further manipulation.
    """
    model = None
    queryset = None
    slug_field = 'slug'
    context_object_name = None
    slug_url_kwarg = 'slug'
    pk_url_kwarg = 'pk'
    query_pk_and_slug = False

    def get_queryset(self, request, **kwargs):
        """
        Return the `QuerySet` that will be used to look up the object.

        This method is called by the default implementation of get_object() and
        may not be called if get_object() is overridden.
        """
        if self.queryset is None:
            if self.model:
                return self.model._default_manager.all()
            else:
                raise ImproperlyConfigured(
                    "%(cls)s is missing a QuerySet. Define "
                    "%(cls)s.model, %(cls)s.queryset, or override "
                    "%(cls)s.get_queryset()." % {
                        'cls': self.__class__.__name__
                    }
                )
        return self.queryset.all()

    def get_object(self, request, **kwargs):
        """
        Return the object the view is displaying.

        Require `self.queryset` and a `pk` or `slug` argument in the URLconf.
        Subclasses can override this to return any object.
        """
        # Use a custom queryset if provided; this is required for subclasses
        # like DateDetailView
        queryset = self.get_queryset(request, **kwargs)
        if queryset is None:
            queryset = self.get_queryset()

        # Next, try looking up by primary key.
        pk = kwargs.get(self.pk_url_kwarg)
        slug = kwargs.get(self.slug_url_kwarg)
        if pk is not None:
            queryset = queryset.filter(pk=pk)

        # Next, try looking up by slug.
        if slug is not None and (pk is None or self.query_pk_and_slug):
            slug_field = self.get_slug_field()
            queryset = queryset.filter(**{slug_field: slug})

        # If none of those are defined, it's an error.
        if pk is None and slug is None:
            raise AttributeError("Generic detail view %s must be called with "
                                 "either an object pk or a slug."
                                 % self.__class__.__name__)

        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                          {'verbose_name': queryset.model._meta.verbose_name})
        return obj

    def get_slug_field(self):
        """Get the name of a slug field to be used to look up by slug."""
        return self.slug_field

    def get_context_object_name(self, obj):
        """Get the name to use for the object."""
        if self.context_object_name:
            return self.context_object_name
        elif isinstance(obj, models.Model):
            return obj._meta.model_name
        else:
            return None

    def get_context_data(self, **kwargs):
        """Insert the single object into the context dict."""
        context = {}
        if self.object:
            context['object'] = self.object
            context_object_name = self.get_context_object_name(self.object)
            if context_object_name:
                context[context_object_name] = self.object
        context.update(kwargs)
        return super().get_context_data(**context)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render(context)

    template_name_field = None
    template_name_suffix = '_detail'

    def get_template_names(self, request, **kwargs):
        """
        Return a list of template names to be used for the request. May not be
        called if render_to_response() is overridden. Return the following list:

        * the value of ``template_name`` on the view (if provided)
        * the contents of the ``template_name_field`` field on the
          object instance that the view is operating upon (if available)
        * ``<app_label>/<model_name><template_name_suffix>.html``
        """
        try:
            names = super().get_template_names(request, **kwargs)
        except ImproperlyConfigured:
            # If template_name isn't specified, it's not a problem --
            # # we just start with an empty list.
            names = [
                *self.get_object_templates(request, **kwargs),
            ]

            # # If self.template_name_field is set, grab the value of the field
            # # of that name from the object; this is the most specific template
            # # name, if given.
            # if request.object and self.template_name_field:
            #     name = getattr(self.object, self.template_name_field, None)
            #     if name:
            #         names.insert(0, name)
            #
            # # The least-specific option is the default <app>/<model>_detail.html;
            # # only use this if the object in question is a model.
            # if isinstance(self.object, models.Model):
            #     object_meta = self.object._meta
            #     names.append("%s/%s%s.html" % (
            #         object_meta.app_label,
            #         object_meta.model_name,
            #         self.template_name_suffix
            #     ))
            # elif hasattr(self, 'model') and self.model is not None and issubclass(self.model, models.Model):
            #     names.append("%s/%s%s.html" % (
            #         self.model._meta.app_label,
            #         self.model._meta.model_name,
            #         self.template_name_suffix
            #     ))
            #
            # # If we still haven't managed to find any template names, we should
            # # re-raise the ImproperlyConfigured to alert the user.
            if not names:
                raise

        return names

    def get_object_templates(self, request, **kwargs):
        return []
