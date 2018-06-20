from collections import OrderedDict

from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from rest_framework import serializers
from rest_framework.relations import HyperlinkedRelatedField

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


class RestAPISerializer(serializers.ModelSerializer):
    """
    An extended HyperlinkedModelSerializer:

    * Puts all relations to external resources on the obj.links attributes
      (including a self link)
    * Foreign key relations produce links on the links attribute
    """

    serializer_related_field = RestAPIRelatedField
    links = serializers.SerializerMethodField()

    # Urls names and lookup
    base_name = None
    detail_url = None
    list_url = None
    lookup_field = None

    # Actions and extra links
    actions = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Define base urls
        request = self.context.get('request')
        if request is None:
            self.url_prefix = ''
        else:
            self.url_prefix = f'{request.scheme}://{request.get_host()}'
        if self.base_name is None:
            cls = type(self)
            name = '%s.%s' % (cls.__module__, cls.__qualname__)
            raise ImproperlyConfigured(
                'Must provide a "base_name" value for the RestAPISerializer '
                'subclass. %s does not define such class attribute.' % name
            )
        base_path = reverse(self.base_name + '-list')
        self.base_url = join_url(self.url_prefix, base_path)

    def get_links(self, obj):
        """
        Return the links dictionary mapping resource names to their
        corresponding links according to HATEAOS.
        """
        return {**self._inner_links(obj), **self._outer_links(obj)}

    def _inner_links(self, obj):
        """
        Return a mapping of all inner hyperlinks in object.
        """

        lookup_field = self.lookup_field
        kwargs = {lookup_field: getattr(obj, lookup_field)}
        self_url = reverse(self.detail_url, kwargs=kwargs)
        self_url = self.url_prefix + self_url

        extra = {action: f'{self_url}{action}/' for action in self.actions}
        return {'self': self_url, **extra}

    def _outer_links(self, obj):
        """
        Return a mapping with all external hyperlinks following from the given
        object.
        """
        links = {}

        for name, params in self.Meta.extra_kwargs.items():
            value = getattr(obj, name)
            lookup_field = params['lookup_field']
            lookup_value = getattr(value, lookup_field)

            kwargs = {lookup_field: lookup_value}
            view_name = params['view_name']
            url = reverse(view_name, kwargs=kwargs)

            links[name] = self.url_prefix + url

        return links
