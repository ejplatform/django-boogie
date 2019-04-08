from sidekick import import_later as _import_later

from .linear_namespace import linear_namespace, linear_namespace_from_sequence

random_name = _import_later(".random_names:random_name", package=__package__)
