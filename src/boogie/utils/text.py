def humanize_name(name):
    """
    "Humanize" camel case or Python variable name.

    Usage:
        >>> humanize_name('SomeName')
        'some name'
    """
    name = name.replace('_', ' ')
    parts = []
    buffer = []
    is_last_lower = False
    for chr in name:
        if chr.isupper():
            if is_last_lower:
                parts.append(''.join(buffer))
                buffer = [chr]
            else:
                buffer.append(chr)
            is_last_lower = False
        else:
            is_last_lower = True
            buffer.append(chr)

    parts.append(''.join(buffer))
    return '-'.join(parts)


def plural(st):
    """
    Convert string into a probable plural form.
    """
    return st + 's'
