from copy import copy

from django.db.models import Model, AutoField, FieldDoesNotExist
from django.urls import reverse
from rest_framework.serializers import SerializerMethodField
from sidekick import lazy

from .serializers import RestAPISerializer, RestAPIInlineSerializer
from .settings import get_url_prefix
from .utils import natural_base_url, viewset_actions
from .viewsets import RestAPIBaseViewSet


class ResourceInfo:
    """
    Stores all information about a resource that is necessary to build the
    corresponding serializer and viewset classes.
    """

    model_name = lazy(lambda self: self.model.__name__)

    @property
    def field_names(self):
        yield from (f.name for f in self.model._meta.fields)

    @property
    def related_field_names(self):
        yield from (name for name, model in self.related_models)

    @property
    def related_models(self):
        for name in self.fields:
            if name in self.properties:
                pass
            try:
                field = self.meta.get_field(name)
            except FieldDoesNotExist:
                continue
            if field.related_model:
                yield name, field.related_model

    @lazy
    def property_methods(self):
        ns = {}
        for name, property in self.properties.items():
            ns[name] = SerializerMethodField()
            ns["get_" + name] = property_method(property, name)
        return ns

    @lazy
    def queryset(self):
        """
        Default queryset for the resource.
        """
        fields = self.related_field_names
        qs = self.model._default_manager.select_related(*fields)
        return self.update_queryset(qs)

    @lazy
    def action_methods(self):
        """
        Methods registered with the @rest_api.action() decorator.
        """
        return viewset_actions(self.actions)

    @lazy
    def detail_actions(self):
        return {k: v for k, v in self.actions.items() if v["args"].get("detail")}

    @lazy
    def serializer_hook_methods(self):
        methods = {}

        if "save" in self.hooks:
            save_hook = wrap_request_instance_method(self.hooks["save"])
            methods["save_hook"] = save_hook

        return methods

    @lazy
    def viewset_hook_methods(self):
        methods = {}
        for hook in ("delete", "query"):
            if hook in self.hooks:
                hook_method = wrap_request_instance_method(self.hooks[hook])
                methods[hook + "_hook"] = hook_method

        return methods

    def __init__(
        self,
        model: Model,
        # Fields
        fields=None,
        exclude=(),
        # Urls and views
        base_url=None,
        base_name=None,
        # Viewset options
        viewset_base=RestAPIBaseViewSet,
        update_queryset=lambda x: x,
        # Serializer options
        serializer_base=None,
        # Other options
        inline=False,
        lookup_field="pk",
    ):

        self.model = model
        self.meta = model._meta
        self._model_fields = {f.name: f for f in self.meta.fields}
        self.inline = inline
        self.lookup_field = lookup_field

        # Field info
        fields = list(fields or fields_from_model(model))
        for field in exclude:
            if field in fields:
                fields.remove(field)
        self.fields = []
        for f in fields:
            self.add_field(f)

        # Url info
        self.base_url = base_url or natural_base_url(model)
        self.base_name = base_name or natural_base_url(model)

        # Hooks
        self.actions = {}
        self.properties = {}
        self.hooks = {}
        self.links = {}

        # Viewsets
        self.viewset_base = viewset_base
        self.update_queryset = update_queryset

        # Serializer
        if serializer_base is None:
            if inline:
                serializer_base = RestAPIInlineSerializer
            else:
                serializer_base = RestAPISerializer
        self.serializer_base = serializer_base

    def copy(self):
        """
        Return a copy of itelf.
        """
        return copy(self)

    def add_hook(self, hook, function):
        if hook not in ("save", "delete", "query"):
            raise ValueError(f"invalid hook: {hook}")
        self.hooks[hook] = function

    def add_field(self, name, check=True):
        """
        Register a new field name.
        """
        if check:
            self.meta.get_field(name)
        if name not in self.fields:
            self.fields.append(name)

    def add_link(self, name, method):
        """
        Register a new field name.
        """
        self.links[name] = method

    def add_property(self, name, method):
        """
        Register a property with the provided name.

        Args:
            name:
                Property name.
            method:
                A function f(obj) -> value that receives a model instance and
                return the corresponding property value.
        """
        self.add_field(name, check=False)
        self.properties[name] = method

    def add_action(self, name, method, **kwargs):
        """
        Register an action with the given name.
        """
        if "list" in kwargs and "detail" in kwargs:
            msg = 'cannot specify both "list" and "detail" parameters ' "simultaneously"
            raise TypeError(msg)
        elif "list" in kwargs:
            kwargs["detail"] = not kwargs.pop("list")
        kwargs.setdefault("detail", True)
        self.actions[name] = {"method": method, "args": kwargs}

    #
    # Info
    #
    def full_base_name(self, version):
        """
        Base name with version information.
        """
        return "%s-%s" % (version, self.base_name)

    def extra_kwargs(self, version):
        """
        extra_kwargs applied on the serializer for references to the resource
        model.
        """
        return {
            "view_name": self.full_base_name(version) + "-detail",
            "lookup_field": self.lookup_field,
        }

    def detail_hyperlink(self, obj, request=None, version=None):
        """
        Return API hyperlink for object.
        """
        attr = self.lookup_field
        kwargs = {attr: getattr(obj, attr)}
        if version:
            view_name = self.full_base_name(version)
        else:
            view_name = self.base_name
        path = reverse(view_name + "-detail", kwargs=kwargs)
        return get_url_prefix(request) + path


#
# Auxiliary functions
#
def fields_from_model(model):
    return [f.name for f in model._meta.fields if not isinstance(f, AutoField)]


def property_method(func, name):
    def method(self, obj):
        return func(obj)

    method.__name__ = method.__qualname__ = "get_" + name
    return method


def wrap_request_instance_method(func):
    return lambda self, request, obj: func(request, obj)
