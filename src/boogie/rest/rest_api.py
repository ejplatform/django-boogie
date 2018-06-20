import logging

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.urls import path, include
from rest_framework import routers

from sidekick import lazy
from .api_info import ApiInfo
from .resource_info import ResourceInfo
from .utils import as_model

log = logging.getLogger('boogie.rest_api')


class RestAPI:
    """
    Base class that stores global information for building an REST API with DRF.
    """
    router_class = routers.DefaultRouter

    @lazy
    def last_version(self):
        versions = set(self.api_registry)
        versions.remove(None)
        return max(versions) if versions else 'v1'

    @lazy
    def urls(self):
        versions = [v for v in self.api_registry if v is not None]
        return [
            *(path(f'{v}/', include(self.get_urls(v))) for v in versions),
            path('', api_root_view(versions)),
        ]

    def __init__(self):
        self._api_info_base = api_info_base = ApiInfo(self)
        self.api_registry = {
            None: self._api_info_base,
            'v1': ApiInfo(self, version='v1', parent=api_info_base),
        }
        self.inlines_registry = {}

    def __call__(self, *args, version=None, inline=False, lookup_field='pk',
                 base_url=None, base_name=None, **kwargs):

        def decorator(cls):
            if not isinstance(cls, type) and not issubclass(type, models.Model):
                msg = f'must decorate a Django model subclass, got {cls}'
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
        if inline:
            self.inlines_registry[model, version] = resource_info
        else:
            info = self.get_api_info(version, create=True)
            info[model] = resource_info
        return resource_info

    #
    # Decorators
    #
    def action(self, model, func=None, *, version=None, name=None, **kwargs):
        """
        Decorator that register a function as an action to the provided
        model.

        Args:
            model:
                A Django model or a string with <app_label>.<model_name>.
            func:
                The function that implements the action.
            name:
                The action name. It is normally derived from the action function
                by simply replacing underscores by dashes in the function
                name.

        Usage:

            .. code-block:: python

                @rest_api.action('auth.User')
                def books(user):
                    return user.user.books.all()
        """

        def decorator(func):
            action_name = name or func.__name__
            info.add_action(action_name, func, **kwargs)
            return func

        info = self.get_resource_info(model, version)
        return decorator if func is None else decorator(func)

    def property(self, model, func=None, *, version=None, name=None):
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

    #
    # Actions
    #
    def serialize(self, obj, request=None, version='v1'):
        """
        Serialize object and return the corresponding JSON structure.
        """

        if isinstance(obj, models.Model):
            model = type(obj)
            many = False
        else:
            model = obj.model
            many = True

        ctx = {'request': request} if request is not None else None
        serializer = self.get_serializer(model, version=version)
        result = serializer(obj, many=many, context=ctx)
        return result.data

    def get_router(self, version='v1'):
        """
        Gets a DRF router object for the given API version.

        Args:
            version: An API version string.
        """
        api_info = self.get_api_info(version)
        router = self.router_class()
        router.root_view_name += '-' + version

        for model, info in sorted(api_info.items(), key=lambda x: x[1].base_url):
            viewset = api_info.viewset_class(model)
            url = api_info.base_url(model)
            base_name = api_info.base_name(model)
            router.register(url, viewset, base_name)
            log.debug('created viewset %s at %s' % (url, base_name))

        return router

    def get_urls(self, version='v1'):
        """
        Return a list of urls to be included in Django's urlpatterns::

        Usage:
            .. code-block:: python

                urlpatterns = [
                    ...,
                    path('api/v1/', include(rest_api.get_urls('v1')))
                ]

        See Also:
            :meth:`get_router`
        """
        return self.get_router(version).urls

    def get_serializer(self, model, version='v1'):
        """
        Return the serializer class for the given model.
        """
        api_info = self.get_api_info(version=version)
        return api_info.serializer_class(model)

    def get_api_info(self, version='v1', create=False):
        """
        Return the ApiInfo instance associated with the given API version.

        If version does not exist and create=True, it creates a new empty
        ApiInfo object.

        Returns an :cls:`ApiInfo` instance.
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

    def get_resource_info(self, model, version='v1'):
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
            A :cls:`ResourceInfo` instance.
        """
        model = as_model(model)
        registry = self.get_api_info(version, create=True)
        try:
            return registry[model]
        except KeyError:
            model_name = model._meta.name
            version_string = '' if not version else ' (%s)' % version
            raise ImproperlyConfigured(
                '{model} is not registered on the API{version}. Please '
                'decorate the model class with the boogie.rest.rest_api() '
                'decorator.'.format(model=model_name, version=version_string)
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

    views = {version: 'api-root-' + version for version in versions}
    return RestApiView.as_view(api_root_dict=views)
