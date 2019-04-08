import contextlib
import io


def humanize_name(name):
    """
    "Humanize" camel case or Python variable name.

    Usage:
        >>> humanize_name('SomeName')
        'some name'
    """
    name = name.replace("_", " ")
    parts = []
    buffer = []
    is_last_lower = False
    for chr in name:
        if chr.isupper():
            if is_last_lower:
                parts.append("".join(buffer))
                buffer = [chr]
            else:
                buffer.append(chr)
            is_last_lower = False
        else:
            is_last_lower = True
            buffer.append(chr)

    parts.append("".join(buffer))
    return " ".join(parts)


def plural(st):
    """
    Convert string into a probable plural form.
    """
    return st + "s"


def indent(text, indent="    "):
    """
    Indent text by the given indentation string.
    """
    return "\n".join(indent + line for line in text.splitlines())


def safe_repr(obj, max_length=None, repr=repr):
    """
    A safe version of repr that is guaranteed to never raise exceptions.
    """
    # noinspection PyBroadException
    try:
        data = repr(obj)
    except Exception as ex:
        cls_name = type(obj).__name__
        ex_name = type(ex).__name__
        data = f"<{cls_name} object [{ex_name}: {ex}]>"

    if max_length is not None and len(data) > max_length:
        data = data[: max_length - 3] + "..."

    return data


def first_line(st):
    """
    Extracts first line of string.
    """
    return st.lstrip().partition("\n")[0]


def dash_case(name):
    """
    Convert a camel case string to dash case.

    Example:
        >>> dash_case('SomeName')
        'some-name'
    """

    letters = []
    for c in name:
        if c.isupper() and letters and letters[-1] != "-":
            letters.append("-" + c.lower())
        else:
            letters.append(c.lower())
    return "".join(letters).replace("_", "-")


def snake_case(name):
    """
    Convert camel case to snake case.
    """
    return dash_case(name).replace("-", "_")


@contextlib.contextmanager
def redirect_stdout(fd=None):
    """
    Redirect stdout to the given file descriptor.

    If not file descriptor is given, creates a StringIO().
    """
    fd = io.StringIO() if fd is None else fd
    with contextlib.redirect_stdout(fd):
        yield fd


@contextlib.contextmanager
def redirect_stderr(fd=None):
    """
    Redirect stderr to the given file descriptor.

    If not file descriptor is given, creates a StringIO().
    """
    fd = io.StringIO() if fd is None else fd
    with contextlib.redirect_stderr(fd):
        yield fd


@contextlib.contextmanager
def redirect_output(fd=None):
    """
    Redirect output to the given file descriptor.

    If not file descriptor is given, creates a StringIO().
    """
    fd = io.StringIO() if fd is None else fd
    with redirect_stdout(fd):
        with redirect_stderr(fd):
            yield fd
