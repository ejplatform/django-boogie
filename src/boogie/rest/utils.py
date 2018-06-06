from enum import Enum
from functools import singledispatch

from rest_framework.utils.encoders import JSONEncoder

from ..utils.text import humanize_name


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
    msg = {'status_code': status_code, 'error': True}
    if len(errors) == 1:
        msg['message'] = errors[0]
    else:
        msg['messages'] = errors
    return msg


def natural_base_url(model):
    """
    Return the natural base url name for the given model:
    * Uses a plural form.
    * Convert CamelCase to dash-case.
    """
    name = dash_case(model.__name__ + 's')
    return humanize_name(name).replace(' ', '-')


def dash_case(name):
    """
    Convert a camel case string to dash case.

    Example:
        >>> dash_case('SomeName')
        'some-name'
    """

    letters = []
    for c in name:
        if c.isupper() and letters and letters[-1] != '-':
            letters.append('-' + c.lower())
        else:
            letters.append(c.lower())
    return ''.join(letters)


def snake_case(name):
    """
    Convert camel case to snake case.
    """
    return dash_case(name).replace('-', '_')


#
# Register converters to special Boogie types
#
def patch_rest_framework_json_encoder():
    """
    Patch rest_framework JSON encoder to accept objects that define a
    __json_default__ method that coerce data to JSON.
    """
    original = JSONEncoder.default

    if getattr(original, 'patched', False):
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

    if hasattr(obj, '__json_default__'):
        return obj.__json_default__()
    else:
        typename = obj.__class__.__name__
        raise TypeError(f"Object of type '{typename}' is not JSON serializable")


@to_json_default.register(Enum)
def enum_to_json(obj):
    return obj.name
