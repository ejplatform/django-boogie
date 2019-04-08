from sidekick import import_later as _import

fragment = _import(".functions:fragment", package=__package__)
invalidate_cache = _import(".functions:invalidate_cache", package=__package__)
