import logging

from django.db.models import fields, Model
from django.urls import register_converter
from django.urls.converters import get_converter

log = logging.getLogger("boogie")

FIELD_TYPES_MAP = {
    # Numeric
    fields.IntegerField: "int",
    fields.SmallIntegerField: "int",
    fields.PositiveSmallIntegerField: "int",
    # UUID
    fields.UUIDField: "uuid",
    # Slugs
    fields.SlugField: "slug",
}


class ModelConverterBase:
    """
    Specialized converter for specific models.

    By default, it will register the

    <app_label.model_name.lookup_value:value>
    """

    model = None
    regex = None
    queryset = None
    base_converter = None
    raw_converter = None
    lookup_field = "pk"

    def to_python(self, path):
        if isinstance(path, Model):
            return path
        value = self.base_converter.to_python(path)
        query = {self.lookup_field: value}
        try:
            return self.queryset.get(**query)
        except self.model.DoesNotExist:
            return None

    def to_url(self, model):
        if isinstance(model, str):
            return model
        return getattr(model, self.lookup_field)


def register_model_converter(
    model, type_name, lookup_field="pk", lookup_type=None, queryset=None
):
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
        queryset:
            An optional queryset used to extract elements from the database.
    """
    class_name = f"{model.__name__}Converter"
    raw_converter = get_lookup_type(lookup_type, model, lookup_field)
    base_converter = get_converter(raw_converter)
    converter = type(
        class_name,
        (ModelConverterBase,),
        {
            "model": model,
            "lookup_field": lookup_field,
            "raw_converter": raw_converter,
            "base_converter": base_converter,
            "regex": base_converter.regex,
            "queryset": model._default_manager if queryset is None else queryset,
        },
    )
    register_converter(converter, type_name)


def get_lookup_type(kind, model, field_name):
    if kind is not None:
        return kind

    if field_name == "pk":
        field = model._meta.pk
    else:
        field = model._meta.get_field(field_name)
    return FIELD_TYPES_MAP.get(type(field), "str")
