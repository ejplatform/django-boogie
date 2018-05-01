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
    name = model._meta.verbose_name_plural or model._meta.model_name
    return humanize_name(name).replace(' ', '-')
