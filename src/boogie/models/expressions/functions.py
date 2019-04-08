from django.db.models import functions

from .combinable import get_comparable_class

concat = get_comparable_class(
    functions.Concat,
    """
Concatenates the values of all given fields or expressions.

Usage:
    concat(F.first_name, ' ', F.last_name)
""",
)

coalesce = get_comparable_class(
    functions.Coalesce,
    """
Chooses the first non-null value from left to right.

Usage:
    coalesce(F.savings_account, F.check_account, 0)
""",
)

greatest = get_comparable_class(
    functions.Greatest,
    """
Chooses the greatest of the given arguments.

Usage:
    greatest(F.savings_account, F.check_account, 0)
""",
)

least = get_comparable_class(
    functions.Least,
    """
Chooses the smallest of the given arguments.

Usage:
    least(F.savings_account, F.check_account, 0)
""",
)

length = get_comparable_class(
    functions.Length,
    """
Returns the length of a string.

Usage:
    length(F.name)
""",
)
