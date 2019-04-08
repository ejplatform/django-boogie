from pprint import pprint

from sidekick import fn

from .utils.text import safe_repr, first_line


#
# Printing
#
@fn
def info(obj, log=print, full=False):
    """
    Display detailed information about object.
    """

    log("=" * 60)
    log("Object:", obj)

    # Print object state
    try:
        dic = obj.__dict__
    except (AttributeError, TypeError):
        pass
    else:
        log("\nDict")
        if full:
            pprint(dic)
        else:
            _log_values(log, dic)

    # Print information about methods
    methods = []
    for attr, method in public_methods(obj):
        doc = method.__doc__ or ""
        if doc:
            methods.append(f"* {attr}: {first_line(doc)}")
        else:
            methods.append(f"* {attr}")
    if methods:
        log("\nMethods:")
        print("\n".join(methods))
    log("-" * 60)


def _log_values(log, values):
    # First print public values
    for k, v in values.items():
        if not k.startswith("_"):
            log(f"* {k}:", safe_repr(v, max_length=50))

    # Then the private ones (only types)
    for k, v in values.items():
        if k.startswith("_"):
            log(f"* {k} ({v.__class__.__name__})")


#
# Tracing
#
def set_trace():
    raise NotImplementedError


def embed():
    raise NotImplementedError


#
# Integration
#
def namespace():
    """
    Return a namespace of useful debug functions.
    """
    import boogie.debug as dbg

    return {
        "info": info,
        "log": print,
        "pprint": pprint,
        "set_trace": set_trace,
        "embed": embed,
        "dbg": dbg,
    }


def enable_debugging(auto=False):
    """
    Register debugging function to builtins.
    """
    import builtins

    # Checks if debugging should be enabled.
    if auto:
        pass

    # Configure environment in "debug" mode.
    for k, v in namespace().items():
        if not hasattr(builtins, k):
            setattr(builtins, k, v)


#
# Utility
#
def public_dir(obj):
    return (attr for attr in dir(obj) if not attr.startswith("_"))


def public_vars(obj):
    for attr in public_dir(obj):
        try:
            yield attr, getattr(obj, attr)
        except AttributeError:
            pass


def public_methods(obj):
    for attr, method in public_vars(obj):
        if callable(method):
            yield attr, method
