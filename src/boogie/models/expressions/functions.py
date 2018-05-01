from django.db.models import functions


def concat(*args):
    """
    Concatenates the values of all given fields or expressions.
    """
    return functions.Concat(*args)


def coalesce(*args):
    """
    Chooses the first non-null value from left to right.

    Usage:
        coalesce(F.savings_account, F.check_account, 0)
    """
    return functions.Coalesce(*args)


def greatest(*args):
    """
    Chooses the greatest of the given values.

    Usage:
        greatest(F.savings_account, F.check_account, 0)
    """
    return functions.Greatest(*args)


def least(*args):
    """
    Chooses the smallest of the given values.

    Usage:
        least(F.savings_account, F.check_account, 0)
    """
    return functions.Least(*args)
