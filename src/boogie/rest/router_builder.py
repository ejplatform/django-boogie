import logging
import operator

from django.utils.functional import cached_property
from lazyutils import delegate_to
from rest_framework import serializers
from rest_framework import viewsets

from .api_info import ApiInfo
from .resource_info import ResourceInfo
from .serializers import RestAPISerializer
from .viewsets import RestAPIViewSet

log = logging.getLogger('boogie.rest_api')


class RouterBuilder:
    """
    Builds the router object for the given API and resource.
    """
    # Delegate to API
    version = delegate_to('api')

    # Delegate to resource
    base_url = delegate_to('resource')
    model = delegate_to('resource')
    model_name = delegate_to('resource')
    fields = delegate_to('resource')
    used_fields = delegate_to('resource')

    # Class constants
    viewset_base_class = RestAPIViewSet
    serializer_base_class = RestAPISerializer

    # Computed properties
    @cached_property
    def base_name(self):
        return self.api.get_base_name(self.model)

    def __init__(self, api: ApiInfo, resource: ResourceInfo):
        self.api = api
        self.resource = resource

    def register_at(self, router):
        """
        Register resource in router.

        Args:
            router: a DRF router object.
        """
        viewset = self.create_viewset()
        base_name = self.base_name
        name = viewset.__name__
        log.debug('created viewset %s at %s' % (name, base_name))
        return router.register(self.base_url, viewset, base_name)

    def get_model_field(self, field):
        for f in self.model._meta.fields:
            if f.name == field:
                return f

    #
    # Viewset
    #
    def create_viewset(self):
        bases = (*self.get_viewset_mixins(), self.viewset_base_class)
        ns = self.get_viewset_namespace()
        class_name = self.model_name + 'ViewSet'
        return type(class_name, bases, ns)

    def get_viewset_base_class(self):
        return viewsets.ModelViewSet

    def get_viewset_mixins(self):
        return ()

    def get_viewset_namespace(self):
        model = self.model
        relation_fields = [
            f.name
            for f in model._meta.fields
            if f.related_model is not None and f.name in self.used_fields
        ]

        return dict(
            Meta=self.get_viewset_meta(),
            serializer_class=self.get_serializer_class(),
            queryset=model._default_manager.select_related(*relation_fields),
        )

    def get_viewset_meta(self):
        extra_kwargs = {f: self.get_serializer_extra_kwargs(f) for f in self.fields}

        return dict(
            model=self.model,
            fields=self.fields,
            extra_kwargs=extra_kwargs,
        )

    #
    # Serializer
    #
    def get_serializer_class(self):
        bases = (*self.get_serializer_mixins(), self.serializer_base_class)
        ns = self.get_serializer_namespace()
        class_name = self.model_name + 'Serializer'
        return type(class_name, bases, ns)

    def get_serializer_mixins(self):
        return ()

    def get_serializer_namespace(self):
        api = self.api
        model = self.model
        meta = model._meta
        all_fields = {f.name: f for f in meta.fields}
        extra = {}

        # Outer relations corresponds to the set of all fields that define
        # relations to external models
        outer_relations = {}
        for field_name in self.used_fields:
            field = all_fields[field_name]
            if field.related_model:
                outer_model = field.related_model
                outer_relations[field_name] = dict(
                    name=self.resource.model_fields[field_name].name,
                    view_name=api.get_base_name(outer_model) + '-detail',
                    lookup_url=api.get_lookup_field(outer_model),
                )

        # Method fields are either register externally with the
        # rest_api.attr(Model) decorator or are created implicilty in external
        # relations
        method_field = serializers.SerializerMethodField
        methods = self.get_serializer_method_fields(outer_relations)
        extra.update({'get_' + name: func for name, func in methods.items()})
        extra.update({name: method_field() for name in methods})

        return dict(
            base_name=self.base_name,
            Meta=self.get_serializer_meta(),
            outer_relations=outer_relations,
            **extra,
        )

    def get_serializer_meta(self):
        # Fields is usually just the plain list of fields. The "links" fields
        # is required
        fields = self.fields
        if 'links' not in fields:
            fields = ['links', *fields]

        # Class extra_kwargs attribute
        extra_kwargs = (
            (f, self.get_serializer_extra_kwargs(f))
            for f in self.fields)
        extra_kwargs = {k: v for k, v in extra_kwargs if v}

        # Create a Meta class object for the serializer
        ns = dict(
            model=self.model,
            fields=fields,
            extra_kwargs=extra_kwargs,
        )
        return type('Meta', (), ns)

    def get_serializer_extra_kwargs(self, field):
        extra_kwargs = {}
        field = self.get_model_field(field)

        if field is None:
            return extra_kwargs

        if field.related_model:
            view_name = self.api.get_base_name(field.related_model) + '-detail'
            extra_kwargs['view_name'] = view_name

        return extra_kwargs

    def get_serializer_method_fields(self, outer_relations=None):
        """
        Return a mapping from all method fields to their corresponding
        get_<> methods.
        """
        # Registered method fields
        method_fields = {
            field: staticmethod(method)
            for field, method in self.resource.properties.items()
        }

        # Fields for outer relations
        for field_name, relation in (outer_relations or {}).items():
            name = relation.get('name', field_name)
            getter = operator.attrgetter(field_name)
            method_fields[name] = staticmethod(lambda obj: str(getter(obj)))

        return method_fields
