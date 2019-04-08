from enum import Enum
from functools import singledispatch, wraps

from django.apps import apps
from django.db import models
from rest_framework.decorators import action as action_decorator
from rest_framework.response import Response
from rest_framework.utils.encoders import JSONEncoder

from ..router.route import as_request_function
from ..utils.text import dash_case, humanize_name


def as_model(model):
    """
    Return a model class from model or string.
    """
    if isinstance(model, str):
        return apps.get_model(model)
    return model


def join_url(head, *args):
    """
    Join url parts. It prevents duplicate backslashes when joining url
    elements.
    """
    if not args:
        return head
    else:
        tail = join_url(*args)
        return f"{head.rstrip('/')}/{tail.lstrip('/')}"


def validation_error(err, status_code=403):
    """
    Return a JSON message describing a validation error.
    """
    errors = err.messages
    msg = {"status_code": status_code, "error": True}
    if len(errors) == 1:
        msg["message"] = errors[0]
    else:
        msg["messages"] = errors
    return msg


def natural_base_url(model):
    """
    Return the natural base url name for the given model:
    * Uses a plural form.
    * Convert CamelCase to dash-case.
    """
    name = dash_case(model.__name__ + "s")
    return humanize_name(name).replace(" ", "-")


#
# Register converters to special Boogie types
#
def patch_rest_framework_json_encoder():
    """
    Patch rest_framework JSON encoder to accept objects that define a
    __json_default__ method that coerce data to JSON.
    """
    original = JSONEncoder.default

    if getattr(original, "patched", False):
        return

    def default(self, obj):
        try:
            return original(self, obj)
        except TypeError:
            return to_json_default(obj)

    JSONEncoder.default = default
    default.patched = True
    default.original = original


@singledispatch
def to_json_default(obj):
    """
    Single dispatch function that register converters of arbitrary Python
    objects to JSON-compatible values.
    """

    if hasattr(obj, "__json_default__"):
        return obj.__json_default__()
    else:
        typename = obj.__class__.__name__
        raise TypeError(f"Object of type '{typename}' is not JSON serializable")


@to_json_default.register(Enum)
def enum_to_json(obj):
    return obj.name


#
# Viewset and serializer builders
#
def viewset_actions(actions):
    """
    Maps action names to decorated actions methods.
    """

    action_fields = {}
    for name, action in actions.items():
        func = action["method"]
        args = action["args"]
        action_fields[name] = action_method(func, name=name, **args)
    return action_fields


def action_method(function, is_method=False, detail=True, name=None, **kwargs):
    """
    Creates a new method decorated with a @action decorator to be inserted
    in a DRF viewset.
    """
    from boogie.rest import rest_api

    function = as_request_function(function)

    def wrap_result(request, result):
        if isinstance(result, Response):
            return result
        elif isinstance(result, (models.Model, models.QuerySet)):
            result = rest_api.serialize(result, request=request)
        return Response(result)

    def method(self, request, **kwargs):
        if is_method:
            result = function(self, request, **kwargs)
        elif detail:
            obj = self.get_object()
            result = function(request, obj)
        else:
            result = function(request)
        return wrap_result(request, result)

    method.__name__ = name or function.__name__
    if name:
        kwargs["url_path"] = name
    method = action_decorator(detail=detail, **kwargs)(method)
    return method


def with_model_cache(func):
    attr = "_%s_cache" % func.__name__

    @wraps(func)
    def method(self, model):
        if self.version is None:
            raise ValueError("cannot construct value if version is None")

        try:
            cache = getattr(self, attr)
        except AttributeError:
            cache = {}
            setattr(self, attr, cache)

        try:
            return cache[model]
        except KeyError:
            cache[model] = result = func(self, model)
            return result

    return method
