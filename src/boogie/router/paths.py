from django.db.models import fields
from django.shortcuts import get_object_or_404
from django.urls import register_converter
from django.urls.converters import get_converter

FIELD_TYPES_MAP = {
    # Numeric
    fields.IntegerField: 'int',
    fields.SmallIntegerField: 'int',
    fields.PositiveSmallIntegerField: 'int',

    # UUID
    fields.UUIDField: 'uuid',

    # Slugs
    fields.SlugField: 'slug',
}


class ModelConverterBase:
    """
    Specialized converter for specific models.

    By default, it will register the

    <app_label.model_name.lookup_value:value>
    """

    model = None
    regex = None
    base_converter = None
    lookup_field = 'pk'

    def to_python(self, path):
        value = self.base_converter.to_python(path)
        return get_object_or_404(self.model, **{self.lookup_field: value})

    def to_url(self, model):
        return getattr(model, self.lookup_field)


def register_model_converter(model, type_name, lookup_field='pk', lookup_type=None):
    """
    Register a converter for the given model.

    Args:
        model:
            A Django model class.
        type_name:
            Converter type name. The type name cannot include colons or angle
            brackets, but something like "auth.user" is ok. This is the
            name used in path expressions to identify the converter like in
            path("profiles/<auth.user:user>", view, ...)
        lookup_field:
            Lookup field used to extract the model instance from the database.
            (defaults to primary key).
        lookup_type:
            Optional converter type of the lookup field. Can be useful for
            things like slugs, but usually can be derived from the lookup_field.
    """
    class_name = f'{model.__name__}Converter'
    base_converter = get_lookup_type(lookup_type, model, lookup_field)
    converter = type(class_name, (ModelConverterBase,), {
        'model': model,
        'lookup_field': lookup_field,
        'base_converter': base_converter,
        'regex': get_converter(base_converter).regex,
    })
    register_converter(converter, type_name)


def get_lookup_type(type, model, field_name):
    if field_name == 'pk':
        field = model._meta.pk
    else:
        field = model._meta.get_field(field_name)

    if type is not None:
        return type
    return FIELD_TYPES_MAP.get(type(field), 'str')
