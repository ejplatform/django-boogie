import base64
import importlib.util
from hashlib import md5


def secret_hash(data):
    """
    Create a secret hash from data.
    """
    strings = []
    for key, value in sorted(data.items()):
        strings.append(key)
        try:
            if isinstance(value, dict):
                value = sorted(value.items())
            if isinstance(value, list):
                value = tuple(value)
            data = hash(value)
            if data != -1:
                strings.append(str(data))
        except TypeError:
            pass
    data = "".join(strings)
    hash_value = md5(data.encode("utf8")).digest()
    return base64.b85encode(hash_value).decode("ascii")


def module_exists(mod, package=None):
    spec = importlib.util.find_spec(mod, package=package)
    return spec is not None


def module_path(mod, package=None):
    spec = importlib.util.find_spec(mod, package=package)
    return spec.origin
