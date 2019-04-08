from collections import deque

from django.utils.translation import ugettext_lazy as _
from hyperpython import Blob
from hyperpython.fragment import fragment as hp_fragment, FragmentNotFound

from .models import Fragment

CACHED_NON_EXISTING = set()
CACHED_FRAGMENTS = {}
CACHE_FRAGMENT_ORDER = deque()
CACHE_MAX_SIZE = 1024
MISSING_FRAGMENT_MSG = _('<div class="error">Missing "{name}" fragment</div>')


def fragment(ref, *, request=None, raises=False, **kwargs):  # noqa: C901
    """
    Return a fragment instance with the given name.
    """
    tried_hyperpython = False

    # Fetch from cache
    try:
        func = CACHED_FRAGMENTS[ref]
    except KeyError:
        pass
    else:
        return func(request=request, **kwargs)

    # If not in cache, test non-existing cache to fast-track to the hyperpython
    # implementation (which usually does not hit the db).
    if ref in CACHED_NON_EXISTING:
        try:
            return hp_fragment(ref, request=request, **kwargs)
        except FragmentNotFound:
            tried_hyperpython = True

    # Now is time to load fragment from the database
    try:
        obj = Fragment.objects.get(ref=ref)
    except Fragment.DoesNotExist:
        CACHED_NON_EXISTING.add(ref)
    else:
        CACHED_FRAGMENTS[ref] = lambda **kwargs: obj.render(**kwargs)
        CACHE_FRAGMENT_ORDER.append(ref)
        while len(CACHED_FRAGMENTS) > CACHE_MAX_SIZE:
            del CACHED_FRAGMENTS[CACHE_FRAGMENT_ORDER.popleft()]

        return obj.render(request=request, **kwargs)

    # Try hyperpython again, if haven't done before
    if not tried_hyperpython:
        try:
            return hp_fragment(ref, request=request, **kwargs)
        except FragmentNotFound:
            if raises:
                raise
    elif raises:
        raise FragmentNotFound(ref)
    return Blob(MISSING_FRAGMENT_MSG.format(name=ref))


def invalidate_cache(name=None):
    """
    Invalidate cache for the given fragment.

    If called without arguments, invalidate cache for all fragments.
    """
    if name is None:
        CACHED_NON_EXISTING.clear()
        CACHED_FRAGMENTS.clear()
    else:
        CACHED_NON_EXISTING.discard(name)
        CACHED_FRAGMENTS.pop(name, None)
        if name in CACHE_FRAGMENT_ORDER:
            CACHE_FRAGMENT_ORDER.remove(name)


fragment.register = hp_fragment.register
