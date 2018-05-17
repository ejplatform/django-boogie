import logging

from django.core.exceptions import ImproperlyConfigured
from django.urls import path, include
from django.utils.functional import cached_property
from rest_framework import routers

from .api_info import ApiInfo
from .resource_info import ResourceInfo
from .router_builder import RouterBuilder

log = logging.getLogger('boogie.rest_api')


class RestAPI:
    router_class = routers.DefaultRouter

    @cached_property
    def last_version(self):
        versions = set(self.registries)
        versions.remove(None)
        return max(versions) if versions else 'v1'

    @cached_property
    def urls(self):
        versions = set(self.registries)
        versions.remove(None)
        if not versions:
            versions = ['v1']

        urlpatterns = []
        for version in sorted(versions):
            router = self.get_router(version)
            urlpatterns.append(
                path(version + '/', include(router.urls))
            )
        urlpatterns.append(
            path('', api_root_view(versions))
        )

        return urlpatterns

    def __init__(self):
        self.registries = {None: {}}

    def __call__(self, *args, **kwargs):
        if args and isinstance(args[0], type):
            return self(*args[1:], **kwargs)(args[0])

        def decorator(cls):
            self.register(cls, *args, **kwargs)
            return cls

        return decorator

    def register(self, model, fields=None, *, version=None, **kwargs):
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


        Returns:
            An EndPointInfo object.
        """
        info = ResourceInfo(model, fields, **kwargs)
        self.registries[version][model] = info

    def get_router(self, version):
        """
        Gets a DRF router object for the given API version.

        Args:
            version: An API versioning string.
        """
        info = api_info(self, version)
        router = self.router_class()
        router.root_view_name += '-' + version
        for resource in info.resources:
            builder = RouterBuilder(info, resource)
            builder.register_at(router)
        return router

    def get_urls(self, version):
        """
        Return a list of urls to be included in Django's urlpatterns::

        Usage:
            .. code-block:: python

                urlpatterns = [
                    ...,
                    path('api/v1/', rest_api.get_urls('v1'))
                ]

        See Also:
            :meth:`get_router`
        """
        return self.get_router(version).urls

    #
    # Decorators
    #
    def action(self, model, name=None, version=None):
        """
        Decorator that register a function as an action to the provided
        model.

        Args:
            model:
                A Django model or a string with <app_label>.<model_name>.
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

    def property(self, model, func=None, *, version=None, name=None):
        """
        Decorator that declares a read-only API property.

        Args:
            model:
                The model name.
            version:
                API version. If ommited, it will be included in all API
                versions.
        """
        info = self.get_model_info(model, version)

        def decorator(func):
            nonlocal name

            name = name or func.__name__
            info.add_property(name, func)
            return func

        if func is not None:
            decorator(func)
            return

        return decorator

    def get_model_info(self, model, version=None):
        registry = self.registries.setdefault(version, {})
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

def api_info(rest_api: RestAPI, version: str) -> ApiInfo:
    """
    Builds an ApiInfo object.
    """
    registry_map = rest_api.registries.get(version, {})
    classes = {info.cls for info in registry_map.values()}
    for k, v in rest_api.registries[None].items():
        if v.model not in classes:
            registry_map[k] = v.copy()
    return ApiInfo(version, registry_map)


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
