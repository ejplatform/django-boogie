from collections import defaultdict
from collections.abc import MutableMapping

CONF_PARAMS = defaultdict(dict)
GLOBAL_PARAMS = defaultdict(dict)


class Params(MutableMapping):
    """
    A dictionary of parameters.

    Keys are searched first in 4 stores (in order):

    * local store
    * configuration store
    * global store
    * defaults values store
    """

    def __init__(self, id, local=(), defaults=()):
        self._id = id
        self._local = dict(local)
        self._conf = CONF_PARAMS[id]
        self._global = GLOBAL_PARAMS[id]
        self._defaults = dict(defaults)
        self._stores = [self._local, self._conf, self._global, self._defaults]

    def __repr__(self):
        return repr(dict(self))

    def __call__(self, **kwargs):
        new_local = dict(self._local, **kwargs)
        return Params(id, new_local, self._defaults)

    def __getitem__(self, key):
        for store in self._stores:
            if key in store:
                return store[key]
        raise KeyError(key)

    def __setitem__(self, key, value):
        self._local[key] = value

    def __delitem__(self, key):
        if key in self._local:
            del self._local[key]
        elif key in self._defaults:
            del self._defaults[key]
        raise KeyError(key)

    def __len__(self):
        return sum(1 for _ in self)

    def __iter__(self):
        used = set()
        for store in self._stores:
            for key in store:
                if key not in used:
                    yield key
                else:
                    used.add(key)


def get_params(id, **kwargs):
    """
    Returns a mapping of parameters defined either in settings.py or by a call
    to the :func:`set_params` function.
    """
    return Params(id, defaults=kwargs)


def set_params(id, **kwargs):
    """
    Declares a mapping of parameters and sets the global values for its keys.
    """
    GLOBAL_PARAMS[id].update(kwargs)
    return Params(id)


def update_configuration(dic):
    """
    Update the CONF_PARAMS variable inplace with the configuration dictionary
    that is usually defined in settings.py.

    Return the update CONF_PARAMS dictionary.
    """

    for id, params in dic.items():
        CONF_PARAMS[id].update(params)

    return CONF_PARAMS
