import logging
from operator import attrgetter
from warnings import warn

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.urls import path, include
from rest_framework import routers
from rest_framework.viewsets import ModelViewSet
from sidekick import lazy

from .api_info import ApiInfo
from .resource_info import ResourceInfo
from .utils import as_model, natural_base_url

log = logging.getLogger("boogie.rest_api")


class RestAPI:
    """
    Base class that stores global information for building an REST API with DRF.
    """

    router_class = routers.DefaultRouter

    @lazy
    def last_version(self):
        versions = set(self.api_registry)
        versions.remove(None)
        return max(versions) if versions else "v1"

    @lazy
    def urls(self):
        versions = [v for v in self.api_registry if v is not None]
        patterns = self.get_urlpatterns
        return [
            *(path(f"{v}/", include(patterns(v))) for v in versions),
            path("", api_root_view(versions)),
        ]

    def __init__(self):
        self._api_info_base = api_info_base = ApiInfo(self)
        self.api_registry = {
            None: self._api_info_base,
            "v1": ApiInfo(self, version="v1", parent=api_info_base),
        }
        self.inlines_registry = {}

    def __call__(
        self,
        *args,
        version=None,
        inline=False,
        lookup_field="pk",
        base_url=None,
        base_name=None,
        **kwargs,
    ):
        def decorator(cls):
            if not isinstance(cls, type) and not issubclass(type, models.Model):
                msg = f"must decorate a Django model subclass, got {cls}"
                raise TypeError(msg)
            kwargs.update(
                version=version,
                inline=inline,
                lookup_field=lookup_field,
                base_name=base_name,
                base_url=base_url,
            )
            self.register(cls, *args, **kwargs)
            return cls

        if len(args) == 1 and isinstance(args[0], type) and not kwargs:
            return decorator(args[0])
        return decorator

    def register(self, model, fields=None, *, version=None, inline=False, **kwargs):
        """
        Register class with the given meta data.

        Args:
            model:
                A Django model
            version:
                Optional API version string (e.g., 'v1'). If not given, it will
                register a resource to all API versions.
            fields:
                The list of fields used in the API. If not given, uses all
                fields.
            exclude:
                A list of fields that should be excluded.
            base_url:
                The base url address in which the resource is mounted. Defaults
                to a dashed case plural form of the model name.
            base_name:
                Base name for the router urls. Router will append suffixes such
                as <base_name>-detail or <base_name>-list. Defaults
                to a dashed case plural form of the model name.
            inline:
                Inline models are not directly part of an API, but can be
                embedded into other resources.

        Returns:
            An ResourceInfo object.
        """
        model = as_model(model)
        kwargs.update(inline=inline)
        resource_info = ResourceInfo(model, fields, **kwargs)
        info = self.get_api_info(version, create=True)
        info.register_resource(model, resource_info, inline=inline)
        return resource_info

    def register_viewset(  # noqa: C901
        self,
        viewset=None,
        base_url=None,
        *,
        version="v1",
        model=None,
        skip_serializer=False,
    ):
        """
        Register a viewset class responsible for handling the given url.

        If a ModelViewSet is given, the viewset is automatically associated
        with a model and registered. Can be used as a decorator if the viewset
        argument is omitted.

        Args:
            viewset:
                Viewset subclass.
            base_url:
                Base url under which the viewset will be mounted. RestAPI can
                infer this URL from the model, when possible.
            version:
                API version name.
            model:
                Model associated with the viewset, when applicable.
            skip_serializer:
                If True, do not register serializer of ModelViewSet subclasses.
        """

        if isinstance(viewset, str) and base_url is None:
            base_url, viewset = viewset, None
        if viewset is None:
            args = locals()
            args.pop("self")
            args.pop("viewset")
            return lambda x: self.register_viewset(x, **args) or x

        api_info = self.get_api_info(version, create=True)

        # Discover the model class
        if model is None and issubclass(viewset, ModelViewSet):
            try:
                model = viewset.queryset.model
            except AttributeError:
                raise ImproperlyConfigured(
                    "could not determine the model of a ModelViewSet subclass. "
                    "Please pass the model explicitly when registering this "
                    "viewset."
                )
        model = as_model(model)

        # Discover url
        if base_url is None and model:
            base_url = natural_base_url(model)
        if base_url is None:
            raise ImproperlyConfigured(
                "could not determine the base_url for this viewset. Please "
                "pass this parameter explicitly when registering the viewset."
            )

        # Create ResourceInfo, if applicable
        if model is not None and skip_serializer:
            kwargs = {"base_url": base_url}

            def update(to, src):
                try:
                    kwargs[to] = src(viewset)
                except AttributeError:
                    pass

            update("fields", attrgetter("Meta.fields"))
            update("base_name", attrgetter("Meta.base_name"))
            update("lookup_field", attrgetter("lookup_field"))

            api_info[model] = ResourceInfo(model, **kwargs)

        # Register resource
        api_info.register_viewset(base_url, viewset)
        if not skip_serializer and issubclass(viewset, ModelViewSet):
            api_info.register_serializer(model, viewset.serializer_class)

    #
    # Decorators
    #
    def action(self, model, func=None, *, version=None, name=None, **kwargs):
        """
        Base implementation of both detail_action and list_action.

        Please use one of those specific methods.
        """

        def decorator(func):
            action_name = name or func.__name__.replace("_", "-")
            info.add_action(action_name, func, **kwargs)
            return func

        info = self.get_resource_info(model, version)
        return decorator if func is None else decorator(func)

    def detail_action(self, model, func=None, **kwargs):
        """
        Register function as an action for a detail view of a resource.

        Decorator that register a function as an action to the provided
        model.

        Args:
            model:
                A Django model or a string with <app_label>.<model_name>.
            func:
                The function that implements the action. It is a
                function that receives a model instance and return a response.
                RestAPI understands the following objects:

                * Django and DRF Response objects
                * A JSON data structure
                * An instance or queryset of a model that can be serialized by
                  the current API (it will serialize to JSON and return this
                  value)

                Exceptions are also converted to meaningful responses of the
                form ``{"error": true, "message": <msg>, "error_code": <code>}``.
                It understands the following exception classes:

                * PermissionError: error_code = 403
                * ObjectNotFound: error_code = 404
                * ValidationError: error_code = 400

                The handler function can optionally receive a "request" as
                first argument. RestAPI inspects function argument names to
                discover which form to call. This strategy may fail if your
                function uses decorators or other signature changing modifiers.
            version:
                Optional API version name.
            name:
                The action name. It is normally derived from the action function
                by simply replacing underscores by dashes in the function
                name.

        Usage:

            .. code-block:: python

                @rest_api.detail_action('auth.User')
                def books(user):
                    return user.user.books.all()

        This creates a new endpoint /users/<id>/books/ that displays all books
        for the given user.
        """
        return self.action(model, func, detail=True, **kwargs)

    def list_action(self, model, func=None, **kwargs):
        """
        Similar to :method:`detail_action`, but creates an endpoint associated
        with a list of objects.

        Usage:

            .. code-block:: python

                @rest_api.detail_action('auth.User')
                def books():
                    return Book.objects.filter(author__in=users)

            The new endpoint is created under /users/books/

        See Also:
            :meth:`detail_action`
        """
        return self.action(model, func, detail=False, **kwargs)

    def property(self, model, func=None, *, version="v1", name=None):
        """
        Decorator that declares a read-only API property.

        Args:
            model:
                The model name.
            version:
                API version. If omitted, it will be included in all API
                versions.
        """

        def decorator(func):
            prop_name = name or func.__name__
            info.add_property(prop_name, func)
            return func

        info = self.get_resource_info(model, version)
        return decorator if func is None else decorator(func)

    def link(self, model, func=None, *, version="v1", name=None):
        """
        Decorator that declares a function to compute a link included into the
        "links" section of the serialized model.

        Args:
            model:
                The model name.
            version:
                API version. If omitted, it will be included in all API
                versions.
        """

        def decorator(func):
            link_name = name or func.__name__
            info.add_link(link_name, func)
            return func

        info = self.get_resource_info(model, version)
        return decorator if func is None else decorator(func)

    #
    # Hooks
    #
    def save_hook(self, model, func=None, *, version="v1"):
        """
        Decorator that registers a hook that is executed when a new object is
        about to be saved. This occurs both during object creation and when it
        is updated. The provided function receives a request and an unsaved
        instance as arguments and must save the instance to the database and
        return it.

        Args:
            model:
                The model name.
            version:
                API version. If omitted, it will be included in all API
                versions.

        Examples:

            .. code-block:: python

                @rest_api.save_hook(Book)
                def save_book(request, book):
                    book.save()  # Don't forget saving the instance!
                    book.owner = request.user
                    return book
        """

        def decorator(func):
            info.add_hook("save", func)
            return func

        info = self.get_resource_info(model, version)
        return decorator if func is None else decorator(func)

    def delete_hook(self, model, func=None, *, version="v1"):
        """
        Decorator that registers a hook that is executed before a new object is
        about to be deleted.

        Deletion can be prevented either by raising an exception (which will
        generate an error response) or silently by not calling the .delete()
        method of a model or queryset.

        Args:
            model:
                The model name.
            version:
                API version. If omitted, it will be included in all API
                versions.

        Examples:

            .. code-block:: python

                @rest_api.delete_hook(Book)
                def delete_book(request, book):
                    if book.user_can_remove(request.user):
                        book.delete()
                    else:
                        raise PermissionError('user cannot delete book!')
        """

        def decorator(func):
            info.add_hook("delete", func)
            return func

        info = self.get_resource_info(model, version)
        return decorator if func is None else decorator(func)

    def query_hook(self, model, func=None, *, version="v1"):
        """
        Decorator that registers a hook that is executed to extract the
        queryset used by the viewset class.

        Args:
            model:
                The model name.
            version:
                API version. If omitted, it will be included in all API
                versions.

        Examples:

            .. code-block:: python

                @rest_api.query_hook(Book)
                def query_hook(request, qs):
                    return qs.all()
            """

        def decorator(func):
            info.add_hook("query", func)
            return func

        info = self.get_resource_info(model, version)
        return decorator if func is None else decorator(func)

    #
    # Actions
    #
    def serialize(self, obj, request=None, version="v1"):
        """
        Serialize object and return the corresponding JSON structure.
        """

        if isinstance(obj, models.Model):
            model = type(obj)
            many = False
        else:
            model = obj.model
            many = True

        ctx = {"request": request} if request is not None else None
        serializer = self.get_serializer(model, version=version)
        result = serializer(obj, many=many, context=ctx)
        return result.data

    def get_hyperlink(self, obj, request=None, version="v1"):
        """
        Return the hyperlink of the given object in the API.
        """
        info = self.get_resource_info(type(obj), version=version)
        return info.detail_hyperlink(obj, request, version)

    def get_router(self, version="v1"):
        """
        Gets a DRF router object for the given API version.

        Args:
            version: An API version string.
        """
        api_info = self.get_api_info(version)
        router = self.router_class()
        router.root_view_name += "-" + version
        entries = sorted(api_info.iter_viewset_items())

        # Registered sorted entries
        for url, viewset in entries:
            base_name = getattr(viewset, "base_name", None)
            router.register(url, viewset, base_name)
            log.debug("created viewset %s at %s" % (url, base_name))
        return router

    def get_urls(self, version="v1"):
        warn("this function is deprecated, please use get_urlpatterns instead.")
        return self.get_router(version).urls

    def get_urlpatterns(self, version="v1"):
        """
        Return a list of urls to be included in Django's urlpatterns::

        Usage:
            .. code-block:: python

                urlpatterns = [
                    ...,
                    path('api/v1/', include(rest_api.get_urlpatterns('v1')))
                ]

        See Also:
            :meth:`get_router`
        """
        return self.get_router(version).urls

    def get_serializer(self, model, version="v1"):
        """
        Return the serializer class for the given model.
        """
        api_info = self.get_api_info(version=version)
        return api_info.serializer_class(model)

    def get_viewset(self, model, version="v1"):
        """
        Return the viewset class for the given model.
        """
        api_info = self.get_api_info(version=version)
        return api_info.viewset_class(model)

    def get_api_info(self, version="v1", create=False):
        """
        Return the ApiInfo instance associated with the given API version.

        If version does not exist and create=True, it creates a new empty
        ApiInfo object.

        Returns an :class:`ApiInfo` instance.
        """
        try:
            registry = self.api_registry[version]
        except AttributeError:
            if not create:
                raise
            info_base = self._api_info_base
            registry = ApiInfo(self, version=version, parent=info_base)
            self.api_registry[version] = registry
        return registry

    def get_resource_info(self, model, version="v1"):
        """
        Return the resource info object associated with the given model. If
        version does not exist, create a new ApiInfo object for the given
        version.

        Args:
            model:
                A model class or a string in the form of 'app_label.model_name'
            version:
                Version string or None for the default api constructor.

        Returns:
            A :class:`ResourceInfo` instance.
        """
        model = as_model(model)
        registry = self.get_api_info(version, create=True)
        try:
            return registry[model]
        except KeyError:
            model_name = model.__name__
            version_string = "" if not version else " (%s)" % version
            raise ImproperlyConfigured(
                "{model} is not registered on the API{version}. Please "
                "decorate the model class with the boogie.rest.rest_api() "
                "decorator.".format(model=model_name, version=version_string)
            )


#
# Utility functions and classes
#
def api_root_view(versions, description=None):
    class RestApiView(routers.APIRootView):
        """
        This is the base entry point for REST resources and provides access to
        all versions of the REST API.
        """

    if description:
        RestApiView.__doc__ = description

    views = {version: "api-root-" + version for version in versions}
    return RestApiView.as_view(api_root_dict=views)
