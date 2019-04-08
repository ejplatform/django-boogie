from django.db import models
from django.db.models import expressions
from django.db.models import functions

from .fix import lookup_method, lookup_property, delegate_to_f_object
from .functions import coalesce, length
from .geo import GeoAttribute


class FMeta(type(models.F)):
    def __getattr__(cls, attr):  # noqa: N805
        return cls(attr)


class F(expressions.Combinable, metaclass=FMeta):
    """
    Replacement for Django's F, Q, and many Func objects.

    Several use cases:

    * Direct value access:
        ``F.user <==> F('user')``
    * Sub-value access:
        ``F.user.name <==> F('user__name')``
    * Queries:
        ``F.user.created > date <==> Q(user__created__gte=date)``
    * SQL Functions:
        ``F.user.created.min() <==> Min('user__created')``
    """

    geo = property(lambda self: GeoAttribute(self))

    def __init__(self, name):
        self._name = name

    def __repr__(self):
        return "F.%s" % (self._name)

    def __str__(self):
        return self._name

    def __getattr__(self, attr):
        return self.getattr(attr)

    asc = delegate_to_f_object("asc")
    desc = delegate_to_f_object("desc")
    resolve_expression = delegate_to_f_object("resolve_expression")
    default_alias = "boogie.F"

    #
    # Comparison operators are not implemented by Combinable objects because
    # this means overloading "==" to output a non-boolean value. This is
    # generally considered to be a bad practice.
    #
    def __eq__(self, other):
        return models.Q(**{self._name: other})

    def __ne__(self, other):
        return ~(self == other)

    __lt__ = lookup_method("lt")
    __le__ = lookup_method("lte")
    __gt__ = lookup_method("gt")
    __ge__ = lookup_method("gte")
    __pos__ = asc
    __neg__ = desc
    __hash__ = lambda self: hash(self._name)

    def __len__(self):
        msg = "len() function not supported, please use F.%s.length() instead."
        raise TypeError(msg % self._name)

    #
    #  Generic functionality
    #
    def getattr(self, attr):
        """
        F.value.getattr('sub_field') <==> F.value.sub_field.

        This method is necessary if attribute name conflicts with some method
        of the F class.
        """
        return type(self)("%s__%s" % (self._name, attr))

    def cast(self, to_type):
        """
        Coerce an expression to a new value type.
        """
        return functions.Cast(self._name, to_type)

    def with_default(self, *args):
        """
        Return value, if not null, or the first non null argument.

        Arguments can be values or other value attributes.

        Usage:
            F.age.with_default(18)
            F.modified.with_default(F.created, now())
        """
        return coalesce(self, *args)

    def in_sequence(self, values):
        """
        Check if value is present in a sequence of values.

        If the passed values is a queryset, it performs a nested query. Nested
        queries can be either slower (typically) or faster than an explicit
        lists depending on the situation and backend.
        """
        return models.Q(**{self._name + "__in": values})

    def in_range(self, start, end):
        """
        Check if value is within the given range.
        """
        return models.Q(**{self._name + "__range": (start, end)})

    #
    # Statistics
    #
    def count(self, distinct=False):
        """
        Number of non-null occurrences of a value in the database.

        If distinct=True, only count distinct values.
        """
        return models.Count(self._name, distinct=distinct)

    def mean(self):
        """
        Mean value of value.
        """
        return setting_attrs(models.Avg(self._name), name="mean")

    def std(self, sample=False):
        """
        Standard deviation of value.

        If sample=True, return the sample standard deviation.
        """
        return models.StdDev(self._name, sample=sample)

    def var(self, sample=False):
        """
        Variance of value.

        If sample=True, return the sample variance.
        """
        return models.Variance(self._name, sample=sample)

    def min(self):
        """
        Minimum value of value.
        """
        return models.Min(self._name)

    def max(self):
        """
        Maximum value of value.
        """
        return models.Max(self._name)

    def sum(self):
        """
        Sum of all values in column.
        """
        return models.Sum(self._name)

    #
    # String manipulation
    #
    def lower(self):
        """
        Converts value value to lowercase.
        """
        return functions.Lower(self._name)

    def upper(self):
        """
        Converts value value to uppercase.
        """
        return functions.Upper(self._name)

    def length(self):
        """
        Return the size of string value.
        """
        return length(self._name)

    def equals(self, value, case=True):
        """
        Compares value with the given value.

        Args:
            value (str of value):
                String value or value expression used for comparison.
            case (bool):
                Set to case=False to perform a case insensitive comparison.
        """
        key = "%s__%s" % (self._name, "exact" if case else "iexact")
        return models.Q(**{key: value})

    def regex(self, regex, case=True):
        """
        Match components with a regex.

        Notice that the details of the regex language are backend specific,
        which makes this lookup not portable.

        Args:
            regex (str):
                Regular expression used to match values.
            case (bool):
                Set to case=False to perform a case insensitive match.
        """
        key = "%s__%s" % (self._name, "regex" if case else "iregex")
        return models.Q(**{key: regex})

    def startswith(self, prefix, case=True):
        """
        Checks if string string value starts with the given prefix.

        If case=False, performs a case insensitive match.
        """
        key = "%s__%s" % (self._name, "startswith" if case else "istartswith")
        return models.Q(**{key: prefix})

    def endswith(self, suffix, case=True):
        """
        Checks if string string value ends with the given suffix.

        If case=False, performs a case insensitive match.
        """
        key = "%s__%s" % (self._name, "endswith" if case else "iendswith")
        return models.Q(**{key: suffix})

    def has_substring(self, sub, case=True):
        """
        Checks if string string value has the given substring.

        If case=False, performs a case insensitive search.
        """
        key = "%s__%s" % (self._name, "contains" if case else "icontains")
        return models.Q(**{key: sub})

    #
    # Datetimes
    #
    @staticmethod
    def now():
        """
        The current date time.

        Usage:
            Events.objects.filter(F.start_time > F.now())
        """
        return functions.Now()

    year = lookup_property("year")
    month = lookup_property("month")
    day = lookup_property("day")
    week = lookup_property("week")
    week_day = lookup_property("week_day")
    hour = lookup_property("hour")
    minute = lookup_property("minute")
    second = lookup_property("second")

    def extract_from_datetime(self, lookup):
        """
        Extract part of a date, time or datetime by name.

        Usually it is more convenient and safe to use the corresponding
        extractor attribute.

        Usage:
            F.value.extract_from_datetime('year') <==> F.value.year
        """
        return functions.Extract(self._name, lookup_name=lookup)

    def trunc_datetime(self, lookup):
        """
        Truncate datetime in the given component.

        Usually it is more convenient and safe to use the corresponding
        truncation method.

        Usage:
            F.value.trunc_datetime('year') <==> F.value.trunc_year()
        """
        return functions.Trunc(self._name, kind=lookup)

    def trunc_year(self):
        """
        Truncates date or datetime at a whole year.
        """
        return functions.TruncYear(self._name)

    def trunc_month(self):
        """
        Truncates date or datetime at a whole month.
        """
        return functions.TruncMonth(self._name)

    def trunc_day(self):
        """
        Truncates date or datetime at a whole day.
        """
        return functions.TruncDay(self._name)

    def trunc_hour(self):
        """
        Truncates time or datetime at a whole hour.
        """
        return functions.TruncHour(self._name)

    def trunc_minute(self):
        """
        Truncates time or datetime at a whole minute.
        """
        return functions.TruncMinute(self._name)

    def trunc_second(self):
        """
        Truncates time or datetime at a whole second.
        """
        return functions.TruncSecond(self._name)

    def trunc_date(self):
        """
        Truncates datetime to the date component.
        """
        return functions.TruncDate(self._name)

    def trunc_time(self):
        """
        Truncates datetime to the time component.
        """
        return functions.TruncTime(self._name)


#
# Utility functions
#
def setting_attrs(obj, **attrs):
    """
    Save all given keyword arguments as attributes to obj and then return obj.
    """
    for k, v in attrs.items():
        setattr(obj, k, v)
    return obj
