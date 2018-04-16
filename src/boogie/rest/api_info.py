from collections import Mapping

from django.utils.functional import cached_property


class ApiInfo(Mapping):
    """
    Stores information about all resources of an specific API version.
    """

    @cached_property
    def resources(self):
        return list(self.registry.values())

    def __init__(self, version: str, registry: dict = None):
        self.version = version
        self.registry = dict(registry or {})

    def __getitem__(self, item):
        return self.registry[item]

    def __len__(self):
        return len(self.registry)

    def __iter__(self):
        return iter(self.registry)

    def get_base_name(self, model):
        """
        Return the base_name string for the given model.
        """
        resource = self.registry[model]
        return '%s-%s' % (self.version, resource.base_name)

    def get_lookup_field(self, model):
        """
        Return the default lookup_field used for the given model.
        """
        return 'pk'
