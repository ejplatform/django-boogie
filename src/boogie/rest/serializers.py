from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from rest_framework import serializers

from .utils import join_url


class RestAPISerializer(serializers.HyperlinkedModelSerializer):
    """
    An extended HyperlinkedModelSerializer:

    * Puts all relations to external resources on the obj.links attributes
      (including a self link)
    * Foreign key relations produce links on the links attribute

    Note:
        The outer_relations mapping maps field names of external relations
        (ForeignKeys, OneToOneFields and ManyToManyFields) into a dictionary
        with the following properties::

            {
                'name': <JSON name of resulting external link>,
                'view_name': <View name for relation>,
                'lookup_field': <Field name used for lookups>,
            }
    """
    links = serializers.SerializerMethodField()
    base_name = None
    detail_actions = ()
    list_actions = ()
    outer_relations = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Define base urls
        request = self.context.get('request')
        if request is None:
            self.url_prefix = ''
        else:
            self.url_prefix = f'{request.scheme}://{request.get_host()}/'
        if self.base_name is None:
            cls = type(self)
            name = '%s.%s' % (cls.__module__, cls.__qualname__)
            raise ImproperlyConfigured(
                'Must provide a "base_name" value for the RestAPISerializer '
                'subclass. %s does not define such class attribute.' % name
            )
        base_path = reverse(self.base_name + '-list')
        self.base_url = join_url(self.url_prefix, base_path)

    def self_url(self, obj):
        """
        Return the absolute path (i.e., without the http://host part)
        of the detail url for the current resource.
        """
        # Obtain absolute path
        lookup_field = (
            getattr(self.Meta, 'extra_kwargs', {})
            .get('url', {})
            .get('lookup_field', 'pk')
        )
        kwargs = {lookup_field: getattr(obj, lookup_field)}
        return join_url(self.url_prefix,
                        reverse(self.base_name + '-detail', kwargs=kwargs))

    def get_links(self, obj):
        """
        Return the links dictionary mapping resource names to their
        corresponding links according to HATEAOS.
        """
        return {**self.inner_links(obj), **self.outer_links(obj)}

    def inner_links(self, obj):
        """
        Return a mapping of all inner hyperlinks in object.
        """
        self_url = self.self_url(obj)
        return dict(
            self=self_url,
            **{action: join_url(self_url, action)
               for action in sorted(self.detail_actions)}
        )

    def outer_links(self, obj):
        """
        Return a mapping with all external hyperlinks following from the given
        object.
        """
        if not self.outer_relations:
            return {}
        links = {}
        for attr, relation in self.outer_relations.items():
            value = getattr(obj, attr)
            lookup_field = relation.get('lookup_field', 'pk')
            lookup_value = getattr(value, lookup_field)
            kwargs = {lookup_field: lookup_value}

            name = relation.get('name', attr)
            view_name = relation['view_name']
            links[name] = join_url(self.url_prefix,
                                   reverse(view_name, kwargs=kwargs))
        return links
