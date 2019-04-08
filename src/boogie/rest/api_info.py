from collections.abc import Mapping

from django.core.exceptions import ImproperlyConfigured
from sidekick import lazy

from boogie.rest.utils import as_model, with_model_cache


class ApiInfo(Mapping):
    """
    Stores information about all resources of an specific API version.

    It stores the API version in an attribute and behaves as a mapping from
    resource to their respective options.
    """

    @lazy
    def resources(self):
        return list(self.values())

    def __init__(self, rest_api, version=None, parent=None):
        self.rest_api = rest_api
        self.version = version
        self.parent = parent
        self.registry = {}
        self.inline_models = {}
        self.explicit_viewsets = {}
        self.serializer_class_cache = {}

    def __getitem__(self, model):
        model = as_model(model)
        result = (
            self.registry.get(model)
            or self.inline_models.get(model)
            or self.parent
            and self.parent.get(model)
        )
        if result is None:
            raise KeyError(model)
        return result

    def __setitem__(self, model, value):
        model = as_model(model)
        if model in self.registry:
            raise KeyError(f"Model {model.__name__} already registered")
        self.registry[model] = value

    def __len__(self):
        n = 0 if self.parent is None else len(self.parent)
        return n + len(self.registry)

    def __iter__(self):
        yield from iter(self.registry)
        if self.parent:
            yield from self.parent

    def __repr__(self):
        data = {model.__name__: info.base_url for model, info in self.registry.items()}
        return "<ApiInfo version=%r, %r>" % (self.version, data)

    def add_hook(self, model, hook, function):
        """
        Register function to the given hook.
        """
        self[model].add_hook(hook, function)

    def base_name(self, model):
        """
        Return the base_name string for the given model.

        base_name is used to name views when the router is constructed.
        """
        return self[model].full_base_name(self.version)

    def base_url(self, model):
        """
        Return the base_name string for the given model.

        base_name is used to name views when the router is constructed.
        """
        return self[model].base_url

    def lookup_field(self, model):
        """
        Return the default lookup_field used for the given model.
        """
        return self[model].lookup_field

    def iter_viewset_items(self):
        """
        Iterates over all tuples of (base_url, viewset) for all models in this
        ApiInfo object.

        This iterator includes classes defined explicitly using register_viewset
        and implicitly by registering models with rest_api.
        """
        # Explicit viewsets
        for url, viewset in self.explicit_viewsets.items():
            yield (url, viewset)

        # Model viewsets
        for model in self:
            viewset = self.viewset_class(model)
            url = self.base_url(model)
            if url not in self.explicit_viewsets:
                yield (url, viewset)

    #
    # Registry
    #
    def register_viewset(self, base_url, viewset):
        """
        Manually associates viewset with the given url.
        """
        self.explicit_viewsets[base_url] = viewset

    def register_serializer(self, model, serializer):
        """
        Manually associates viewset with the given url.
        """
        model = as_model(model)
        self.serializer_class_cache[model] = serializer

    def register_resource(self, model, info, inline=False):
        """
        Register resource info object for model.
        """
        if inline:
            self.inline_models[model] = info
        else:
            self[model] = info

    #
    # Viewset class builder
    #
    def extra_kwargs(self, model):
        """
        Generate extra_kwargs options for the given model.
        """
        extra_kwargs = {}
        info = self[model]

        for name, related in info.related_models:
            try:
                resource_info = self[related]
            except KeyError:
                raise ImproperlyConfigured(
                    f"{model.__name__} references a {related.__name__} field as "
                    f"{name}. This model is not registered on the api and "
                    f"therefore cannot be included as reference."
                )
            extra = resource_info.extra_kwargs(self.version)
            extra_kwargs[name] = extra
        return extra_kwargs

    @with_model_cache
    def viewset_class(self, model):
        """
        Return a viewset class for the given model.
        """

        info = self[model]
        extra = self.extra_kwargs(model)

        bases = as_bases(info.viewset_base)
        name = info.model.__name__ + "ViewSet"
        base_name = self.base_name(model)

        namespace = {
            "Meta": viewset_meta(info, extra),
            "queryset": info.queryset,
            "serializer_class": self.serializer_class(model),
            "lookup_field": info.lookup_field,
            "base_name": base_name,
            "api_version": self.version,
            **info.action_methods,
            **info.viewset_hook_methods,
        }

        return type(name, bases, namespace)

    @with_model_cache
    def serializer_class(self, model):
        """
        Return the serializer class for the given model.
        """

        info = self[model]
        extra = self.extra_kwargs(model)

        bases = as_bases(info.serializer_base)
        name = info.model.__name__ + "Serializer"
        base_name = self.base_name(model)

        namespace = {
            "Meta": serializer_meta(info, extra),
            "base_name": base_name,
            "detail_url": base_name + "-detail",
            "list_url": base_name + "-list",
            "lookup_field": info.lookup_field,
            "actions": list(info.detail_actions),
            "api_version": self.version,
            "explicit_links": tuple(info.links.items()),
            **info.property_methods,
            **info.serializer_hook_methods,
        }

        return type(name, bases, namespace)


#
# Serializer class builder
#
def api_info(rest_api, version) -> ApiInfo:
    """
    Builds an ApiInfo object.
    """
    registry_map = rest_api.registries.get(version, {})
    classes = {info.cls for info in registry_map.values()}
    for k, v in rest_api.registries[None].items():
        if v.model not in classes:
            registry_map[k] = v.copy()
    return ApiInfo(version, registry_map)


def as_bases(bases):
    if isinstance(bases, type):
        return (bases,)
    return tuple(bases)


def viewset_meta(info, extra_kwargs):
    """
    Meta class for ViewSet.
    """
    return type(
        "Meta",
        (),
        {"model": info.model, "fields": info.fields, "extra_kwargs": extra_kwargs},
    )


def serializer_meta(info, extra_kwargs):
    """
    Meta class for Serializer class.
    """
    return type(
        "Meta",
        (),
        {
            "model": info.model,
            "fields": ["links", *info.fields],
            "extra_kwargs": extra_kwargs,
        },
    )
