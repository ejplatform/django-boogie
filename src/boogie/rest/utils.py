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
