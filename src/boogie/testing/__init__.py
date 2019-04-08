from sidekick import import_later

# Function importer
_function = lambda x: import_later(x, package=__package__)

# Lazy imports of checker functions
check_link_errors = _function(".crawler:check_link_errors")
factory = _function(".factories:factory")
