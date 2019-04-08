import sidekick as sk

from django import http

BOOGIE_VIEW_MIDDLEWARES = {}
NOTGIVEN = object()


def groups_required(groups, **kwargs):
    """
    Return a middleware that validates if the current user belongs to all of
    the provided groups.
    """
    kwargs.setdefault("message", "Insufficient permissions")
    return access_control(lambda r: r.user.has_groups(groups), **kwargs)


def perms_required(perms, *, fn=None, **kwargs):
    """
    Return a middleware that validates if the current user has the given
    permissions.
    """
    kwargs.setdefault("message", "Insufficient permissions")
    if fn:
        return access_control(lambda r: r.user.has_perms(perms, fn(r)), **kwargs)
    else:
        return access_control(lambda r: r.user.has_perms(perms), **kwargs)


def staff_required(**kwargs):
    """
    Return a middleware that validates if the current user is staff.
    """
    kwargs.setdefault("message", "Insufficient permissions")
    return access_control(lambda r: r.user.is_staff, **kwargs)


def login_required(login_url=None, **kwargs):
    """
    Return a middleware that validates if the current user is authenticated.
    """
    if login_url is False:
        kwargs.setdefault("message", "Requires login")
        return access_control(lambda r: r.user.is_authenticated, **kwargs)

    from django.contrib.auth.decorators import login_required

    def middleware(get_response):
        return login_required(login_url=login_url, **kwargs)(get_response)

    return middleware


def check_rule(rule, fn: callable = None, **kwargs):
    """
    Return a middleware that validates if the current user respects the
    given rule.
    """
    import rules

    if fn is None:
        test = lambda r: rules.test_rule(rule, r.user)
    else:
        test = lambda r: rules.test_rule(rule, r.user, fn(r))
    return access_control(test, **kwargs)


def access_control(
    grant_access, response_type=http.HttpResponseForbidden, message="Not allowed"
):
    def middleware(get_response):
        def handler(request):
            if grant_access(request):
                return get_response(request)
            return response_type(message)

        return handler

    return middleware


def unpoly_middleware(get_response):
    """
    Add unpoly headers to request and response objects.
    """

    def handler(request):
        # Read request headers and creates the request.up object
        value = request.META.get
        request.up = sk.record(
            location=value("X-Up-Location"),
            target=value("X-Up-Target"),
            fail_target=value("X-Up-Fail-Target"),
            validate=value("X-Up-Validate"),
        )

        # Handle response and extract title from the context
        response = get_response(request)
        if hasattr(response, "context"):
            title = request.context.get("title")
            if title:
                response.META.setdefault("X-Up-Title", title)

        return response

    return handler


BOOGIE_VIEW_MIDDLEWARES.update(
    {
        "staff_required": staff_required(),
        "login_required": login_required(),
        "unpoly": unpoly_middleware,
    }
)
