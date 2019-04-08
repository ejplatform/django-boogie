from django.conf import settings as _settings

BOOGIE_REST_API_SCHEME = getattr(_settings, "BOOGIE_REST_API_SCHEME", None)


def get_scheme(request):
    return BOOGIE_REST_API_SCHEME or request.scheme


def get_url_prefix(request):
    if request is None:
        return ""
    return f"{get_scheme(request)}://{request.get_host()}"
