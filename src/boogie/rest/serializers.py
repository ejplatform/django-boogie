import traceback
from collections import OrderedDict

from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from rest_framework import serializers
from rest_framework.relations import HyperlinkedRelatedField
from rest_framework.serializers import raise_errors_on_nested_writes
from rest_framework.utils import model_meta
from sidekick import lazy

from .settings import get_url_prefix
from .utils import join_url


class RestAPIRelatedField(HyperlinkedRelatedField):
    def to_internal_value(self, data):
        return self.get_queryset().get(**{self.lookup_field: data})

    def get_choices(self, cutoff=None):
        queryset = self.get_queryset()
        if queryset is None:
            # Ensure that field.choices returns something sensible
            # even when accessed with a read-only field.
            return {}

        if cutoff is not None:
            queryset = queryset[:cutoff]

        return OrderedDict(
            (getattr(item, self.lookup_field), self.display_value(item))
            for item in queryset
        )

    def to_representation(self, value):
        return str(value)

    def use_pk_only_optimization(self):
        return False


class WithLinksSerializerMixin(serializers.Serializer):
    serializer_related_field = RestAPIRelatedField
    links = serializers.SerializerMethodField()
    api_version = None

    # Actions and extra links
    explicit_links = ()

    @lazy
    def request(self):
        return self.context["request"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Define base urls
        request = self.request
        if request is None:
            self.url_prefix = ""
        else:
            self.url_prefix = get_url_prefix(request)

    def get_links(self, obj):
        """
        Return the links dictionary mapping resource names to their
        corresponding links according to HATEAOS.
        """
        return {
            **self._inner_links(obj),
            **self._explicit_links(obj),
            **self._outer_links(obj),
        }

    def _inner_links(self, obj):
        return {}

    def _explicit_links(self, obj):
        """
        Return a mapping with all explicitly registered hyperlinks.
        """
        request = self.request
        return {name: func(request, obj) for name, func in self.explicit_links}

    def _outer_links(self, obj):
        """
        Return a mapping with all external hyperlinks following from the given
        object.
        """
        links = {}

        for name, params in self.Meta.extra_kwargs.items():
            value = getattr(obj, name)
            lookup_field = params["lookup_field"]
            lookup_value = getattr(value, lookup_field)

            kwargs = {lookup_field: lookup_value}
            view_name = params["view_name"]
            url = reverse(view_name, kwargs=kwargs)

            links[name] = self.url_prefix + url

        return links


class RestAPISerializer(WithLinksSerializerMixin, serializers.ModelSerializer):
    """
    An extended HyperlinkedModelSerializer:

    * Puts all relations to external resources on the obj.links attributes
      (including a self link)
    * Foreign key relations produce links on the links attribute
    """

    # Urls names and lookup
    base_name = None
    detail_url = None
    list_url = None
    lookup_field = None

    # Actions and extra links
    actions = ()
    explicit_links = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.base_name is None:
            cls = type(self)
            name = "%s.%s" % (cls.__module__, cls.__qualname__)
            raise ImproperlyConfigured(
                'Must provide a "base_name" value for the RestAPISerializer '
                "subclass. %s does not define such class attribute." % name
            )
        base_path = reverse(self.base_name + "-list")
        self.base_url = join_url(self.url_prefix, base_path)

    def _inner_links(self, obj):
        """
        Return a mapping of all inner hyperlinks in object.
        """

        lookup_field = self.lookup_field
        kwargs = {lookup_field: getattr(obj, lookup_field)}
        self_url = reverse(self.detail_url, kwargs=kwargs)
        self_url = self.url_prefix + self_url

        extra = {action: f"{self_url}{action}/" for action in self.actions}
        return {"self": self_url, **extra}

    #
    # Overloads serializer methods
    #
    def create(self, validated_data):
        # We cannot call the super method because DRF explicitly calls
        # manager.create() inside the method. This is essentially the
        # same method in ModelSerializer, but instead of creating the object
        # directly, it uses the save_hook method.
        raise_errors_on_nested_writes("create", self, validated_data)

        model_class = self.Meta.model

        # Remove many-to-many relationships from validated_data.
        # They are not valid arguments to the default `.create()` method,
        # as they require that the instance has already been saved.
        info = model_meta.get_field_info(model_class)
        many_to_many = {}
        for field_name, relation_info in info.relations.items():
            if relation_info.to_many and (field_name in validated_data):
                many_to_many[field_name] = validated_data.pop(field_name)

        try:
            instance = model_class(**validated_data)
        except TypeError:
            tb = traceback.format_exc()
            msg = (
                "Got a `TypeError` when saving object. "
                "This may be because you have a writable field on the "
                "serializer class that is not a valid argument to the "
                "object constructor. You may need to make the field "
                "read-only, or register a save hook function to handle "
                "this correctly.\nOriginal exception was:\n %s" % tb
            )
            raise TypeError(msg)
        else:
            instance = self.save_hook(self.request, instance)

        # Save many-to-many relationships after the instance is created.
        if many_to_many:
            for field_name, value in many_to_many.items():
                field = getattr(instance, field_name)
                field.set(value)

        return instance

    def update(self, instance, validated_data):
        raise_errors_on_nested_writes("update", self, validated_data)
        info = model_meta.get_field_info(instance)

        # Simply set each attribute on the instance, and then save it.
        # Note that unlike `.create()` we don't need to treat many-to-many
        # relationships as being a special case. During updates we already
        # have an instance pk for the relationships to be associated with.
        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                field = getattr(instance, attr)
                field.set(value)
            else:
                setattr(instance, attr, value)

        return self.save_hook(self.request, instance)

    #
    # Hooks
    #
    def save_hook(self, request, instance):
        instance.save()
        return instance


class RestAPIInlineSerializer(WithLinksSerializerMixin, serializers.ModelSerializer):
    """
    Base serializer class for inline models.
    """
