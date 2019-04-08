import collections.abc
from functools import lru_cache, partial, singledispatch

from django.db import models
from django.db.models.query import ValuesListIterable, BaseIterable
from sidekick import lazy, itertools, import_later, alias

from boogie.models.methodregistry import get_queryset_attribute
from boogie.models.utils import LazyMethod
from .expressions import F
from ..utils.linear_namespace import linear_namespace

F_EXPR_TYPE = type(F.some_attr > 0)

# LAZY IMPORTS
# Useful queryset methods
# import bulk_update.manager
# import manager_utils
pd = import_later("pandas")


# noinspection PyProtectedMember,PyUnresolvedReferences
class QuerySet(models.QuerySet):
    """
    Boogie's drop in replacement to Django's query sets.

    It extends the query set API with a Pydata-inspired interface to select
    data.
    """

    # Manager utils
    id_dict = LazyMethod("manager_utils:ManagerUtilsMixin.id_dict")
    bulk_upsert = LazyMethod("manager_utils:ManagerUtilsMixin.bulk_upsert")
    sync = LazyMethod("manager_utils:ManagerUtilsMixin.sync")
    upsert = LazyMethod("manager_utils:ManagerUtilsMixin.upsert")
    get_or_none = LazyMethod("manager_utils:ManagerUtilsMixin.get_or_none")
    single = LazyMethod("manager_utils:ManagerUtilsMixin.single")

    # Bulk update from manager utils is very limited, we use the implementation
    # in the django-bulk-update package.
    bulk_update = LazyMethod("bulk_update.manager:BulkUpdateManager.bulk_update")

    # Properties
    index = property(lambda self: Index(self))
    _selected_column_names = None

    # Class methods
    def as_manager(cls):
        # Overrides to use Boogie manager instead of the default manager
        from .manager import Manager

        manager = Manager.from_queryset(cls)()
        manager._built_with_as_manager = True
        return manager

    as_manager.queryset_only = True
    as_manager = classmethod(as_manager)

    new = alias("model")

    def __getitem__(self, item):
        # 1D indexing is delegated to Django. We extend it with some
        # idioms that preserve backwards compatibility
        #
        # We keep Django's behavior in all of the following cases (a, b >= 0):
        # * qs[a]
        # * qs[a:b]
        #
        # Small extensions:
        # * qs[-a] -> fetch from last
        # * qs[0:-b] -> specify a index from first to last
        #
        # Larger extensions:
        # * qs[set] -> fetch elements in the given pk set
        # * qs[list] -> fetch specified elements by pk in order
        return get_queryset_item(item, self)

    def __setitem__(self, item, value):
        # Similarly to getitem, we dispatch for the 1d and 2d indexing
        # functions
        if not isinstance(item, tuple):
            return setitem_1d(self, item, value)

        try:
            row, col = item
        except IndexError:
            raise TypeError("only 1d or 2d indexing is allowed")

        return setitem_2d(self, row, col, value)

    def __getattr__(self, attr):
        value = get_queryset_attribute(self, attr)
        if value is NotImplemented:
            raise AttributeError(attr)
        return value

    def update_item(self, pk, **kwargs):
        """
        Updates a single item in the queryset.
        """
        return self.filter(pk=pk).update(**kwargs)

    update_item.alters_data = True

    #
    # Enhanced API
    #
    def select_columns(self, *fields):
        """
        Similar to .values_list(*fields)
        """
        return select_columns(self, list(fields))

    def annotate_verbose(self, **fields):
        """
        Annotate given fields with their verbose versions.
        """
        raise NotImplementedError

    def auto_annotate_verbose(self, *fields):
        raise NotImplementedError

    def values(self, *fields, verbose=False, **expressions):
        if verbose:
            return self.auto_annotate_verbose(fields)

        qs = super().values(*fields, **expressions)
        fields = fields + tuple(expressions.keys())
        return self._mark_column_names(fields, qs)

    def values_list(self, *fields, verbose=False, **kwargs):
        if verbose:
            return self.auto_annotate_verbose(fields)
        qs = super().values_list(*fields, **kwargs)
        return self._mark_column_names(fields, qs)

    def _filter_or_exclude(self, negate, *args, **kwargs):
        if args and getattr(args[0], "comparable_expression", False):
            expr, *args = args
            name = f"filter_{id(expr)}"
            kwargs[name] = True
            qs = self.annotate(**{name: expr})
            # noinspection PyProtectedMember
            return qs._filter_or_exclude(negate, *args, **kwargs)
        return super()._filter_or_exclude(negate, *args, **kwargs)

    def _mark_column_names(self, columns, qs=None):
        qs = self if qs is None else qs
        qs._selected_column_names = columns
        return qs

    #
    # Pandas data frame and numpy array APIs
    #
    def dataframe(
        self, *fields, index=None, verbose=False
    ) -> "pd.DataFrame":  # noqa: F821
        """
        Convert query set to a Pandas data frame.

        If fields are given, it uses a similar semantics as .values_list(),
        otherwise, it uses the selected fields or the complete set of fields.

        Args:
            index:
                Name of index column (defaults to primary key).
            verbose (bool):
                If given, prints foreign keys ad choices using human readable
                names.
        """
        if not fields:
            if self._selected_column_names:
                fields = self._selected_column_names
            else:
                fields = [
                    f.name
                    for f in self.model._meta.fields
                    if index is None and not f.primary_key
                ]
        elif len(fields) == 1 and isinstance(fields[0], collections.Mapping):
            field_map = fields[0]
            df = self.dataframe(*field_map.values(), index=index, verbose=verbose)
            df.columns = field_map.keys()
            return df

        # Build data frame
        if index is None:
            index = self.model._meta.pk.name

        data = list(self.values_list(index, *fields, verbose=verbose))
        df = pd.DataFrame(data, columns=["__index__", *fields])
        df.index = df.pop("__index__")
        df.index.name = index
        return df

    def pivot_table(
        self, index, columns, values, verbose=False, dropna=False, fill_value=None
    ):
        """
        Creates a pivot table from this queryset.

        Args:
            index:
                Field used to define the pivot table indexes (rows names).
            columns:
                Field used to populate the different columns.
            values:
                Field used to fill table with values.
            dropna (bool):
                If True (default), exclude columns whose entries are all NaN.
            fill_value:
                Value to replace missing values with.
            verbose (bool):
                If given, prints foreign keys ad choices using human readable
                names.

        """
        df = self.dataframe(index, columns, values, verbose=verbose)
        if df.shape[0] == 0:
            dtype = float if fill_value is None else type(fill_value)
            df = pd.DataFrame(dtype=dtype, index=pd.Index([], dtype=int))
            df.index.name = index
            return df
        return df.pivot_table(
            index=index,
            columns=columns,
            values=values,
            dropna=dropna,
            fill_value=fill_value,
        )

    def update_from_dataframe(self, dataframe, batch_size=None, in_bulk=True):
        """
        Persist data frame data to the database. Data frame index must
        correspond to primary keys of existing objects.

        Args:
            dataframe:
                A pandas data frame
            in_bulk (bool):
                If True (default), save values in bulk.
            batch_size:
                If saving in bulk, defines the size of each batch that touches
                the database. This avoids creating very long SQL commands that
                can halt the database for a perceptible amount of time.
        """
        objects = []
        fields = dataframe.columns
        add_object = objects.append
        new_object = self.model

        for pk, row in zip(dataframe.index, dataframe.to_dict("records")):
            row.setdefault("pk", pk)
            add_object(new_object(**row))

        if in_bulk:
            self.bulk_update(objects, update_fields=list(fields), batch_size=batch_size)
        else:
            for obj in objects:
                obj.save()

    def extend_dataframe(self, df, *fields, verbose=False) -> "pd.DataFrame":
        """
        Returns a copy of dataframe that includes columns computed from the
        given fields.
        """
        extra = (
            self.filter(pk__in=set(df.index))
            .distinct()
            .dataframe(*fields, verbose=verbose)
        )
        extra.index.name = df.index.name
        new = pd.DataFrame(df)
        for k, v in extra.items():
            new[k] = v
        return new

    #
    # Selecting parts of the dataframe
    #
    def head(self, n=5):
        """
        Select the first n rows in the query set.
        """
        return self[:n]

    def tail(self, n=5):
        """
        Select the last n rows in the query set.
        """
        return self[-n:]

    #
    # Transformations
    #
    def map(self, func, *args, **kwargs):
        """
        Map function to each element returned by the dataframe.
        """

        if args or kwargs:
            orig = func
            func = lambda x: orig(*args, **kwargs)

        clone = self.all()
        iter_cls = MapIterable.as_iterable_class(func, clone._iterable_class)
        clone._iterable_class = iter_cls
        return clone

    def annotate_attr(self, **kwargs):
        """
        Like Django's builtin annotate, but instead of operating in SQL-level,
        it annotates the resulting Python objects.
        """

        def annotator(obj):
            for k, v in kwargs.items():
                if callable(v):
                    v = v(obj)
                setattr(obj, k, v)
            return obj

        return self.map(annotator)


#
# Auxiliary classes
# ----------------------------------------------------------------------------
class QuerysetSequence(collections.abc.Sequence):
    @staticmethod
    def prepare(queryset):
        return queryset

    _prepared = lazy(lambda self: self.prepare(self.queryset))

    def __init__(self, queryset):
        self.queryset = queryset

    def __iter__(self):
        return iter(self._prepared)

    def __len__(self):
        return len(self._prepared)

    def __getitem__(self, item):
        return self._prepared[item]

    def __repr__(self):
        return "%s(%s)" % (type(self).__name__, list(self))


class Index(QuerysetSequence):
    """
    Returns an index with the primary keys of all elements.
    """

    @staticmethod
    def prepare(qs):
        return qs.values_list("pk", flat=True)


class RowIterable(ValuesListIterable):
    """
    Iterable returned by QuerySet.values_list(named=True) that yields a
    namedtuple for each row.
    """

    @staticmethod
    @lru_cache()
    def _create_row_class(names):
        return linear_namespace("Row", names)

    def __init__(self, *args, **kwargs):
        self.field_names = kwargs.pop("field_names", None)
        super().__init__(*args, **kwargs)

    def __iter__(self):
        queryset = self.queryset
        if self.field_names:
            names = self.field_names
        elif queryset._fields:
            names = queryset._fields
        else:
            query = queryset.query
            names = list(query.extra_select)
            names.extend(query.values_select)
            names.extend(query.annotation_select)

        new = self._create_row_class(tuple(names))
        for row in super().__iter__():
            yield new(*row)


class MapIterable(BaseIterable):
    @classmethod
    def as_iterable_class(cls, func, iterable_class):
        return lambda *args, **kwargs: cls(
            func, iterable_class(*args, **kwargs), *args, **kwargs
        )

    def __init__(self, func, iterable, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.function = func
        self.iterable = iterable

    def __iter__(self):
        func = self.function
        for elem in self.iterable:
            yield func(elem)


#
# Getitem auxiliary functions
# ----------------------------------------------------------------------------


def getitem_2d(qs, rows, cols):
    """
    Extract elements from queryset possibly filtering specific rows
    or columns.

    The first index selects rows and the second columns.
    """
    # First we filter the rows
    if is_vector_row_access(rows):
        qs = filter_queryset(qs, rows)
        return select_columns(qs, cols)
    else:
        qs = qs.filter(pk=rows)
        return select_columns(qs, cols)[0]


def is_vector_row_access(row):
    """
    Return True to all types that select multiple rows.
    """
    return isinstance(row, (list, slice, QuerySet, F_EXPR_TYPE))


def filter_queryset(qs, rows):
    """
    Extended ways to filter a queryset.
    """

    # Filter by pk
    if isinstance(rows, list):
        model = qs.model
        pks = {x.pk if isinstance(x, model) else x for x in rows}
        return qs.filter(pk__in=pks)

    elif isinstance(rows, slice):
        if rows == slice(None, None, None):
            return qs
        raise IndexError("invalid column slice: %s" % rows)

    elif isinstance(rows, QuerySet):
        return qs & rows

    elif isinstance(rows, F_EXPR_TYPE):
        return qs.filter(rows)

    raise TypeError("invalid row selector: %r" % rows.__class__.__name__)


def select_columns(qs, cols):
    if isinstance(cols, list):
        qs = qs.values_list(*cols, flat=False)
        field_names = get_column_names(cols, qs)
        qs._iterable_class = partial(RowIterable, field_names=field_names)
        return qs

    elif isinstance(cols, slice):
        if cols == slice(None, None, None):
            return qs
        raise IndexError("invalid column slice: %s" % cols)

    elif isinstance(cols, (str, F, models.F)):
        return qs.values_list(cols, flat=True)

    raise TypeError("invalid column selector: %r" % cols.__class__.__name__)


def get_column_names(cols, qs):
    """
    Return a list of valid field names for the given columns.
    """
    names = []
    append = names.append
    for col in cols:
        if isinstance(col, str):
            name = col
        elif isinstance(col, F):
            name = col._name
        else:
            raise TypeError("invalid column", col)
        append(name)
    return names


#
# Setitem auxiliary functions
# ----------------------------------------------------------------------------
@singledispatch
def get_queryset_item(item, qs):
    raise TypeError(f"Invalid index type: {item.__class__.__name__}")


@get_queryset_item.register(tuple)
def _(item, qs):
    try:
        row, col = item
    except IndexError:
        raise TypeError("only 1d or 2d indexing is allowed")
    return getitem_2d(qs, row, col)


@get_queryset_item.register(int)
def _(n, qs):
    if n >= 0:
        return super(QuerySet, qs).__getitem__(n)
    else:
        rev = qs.reverse() if qs.ordered else qs.order_by("-id")
        return rev[abs(n) - 1]


@get_queryset_item.register(slice)
def _(slice, qs):
    start, stop, step = slice.start, slice.stop, slice.step
    if step is None and (start is None or start >= 0) and (stop is None or stop >= 0):
        return super(QuerySet, qs).__getitem__(slice)
    elif stop <= 0:
        if start != 0 and start is not None:
            raise ValueError(
                "negative index are only allowed if starting from the "
                "beginning of the queryset"
            )
        return qs.reverse()[abs(stop) - 1 :].reverse()


@get_queryset_item.register(set)
def _(set_index, qs):
    return qs.filter(pk__in=set_index)


@get_queryset_item.register(list)
def _(lst, qs):
    raise NotImplementedError("use set instead of list")


def setitem_1d(qs, item, value):
    raise TypeError("invalid index type: %r" % item.__class__.__name__)


def setitem_2d(qs: QuerySet, rows, cols, value):
    if is_vector_row_access(rows):
        raise NotImplementedError
    elif isinstance(cols, str):
        return qs.update_item(rows, **{cols: value})
    elif isinstance(cols, list):
        cols = map(as_col_name, cols)
        mapping = dict(zip(cols, value))
        return qs.update_item(rows, **mapping)
    raise NotImplementedError


def set_columns(qs: QuerySet, cols, value):
    raise TypeError("invalid column selector: %r" % cols.__class__.__name__)


def as_col_name(obj):
    """Coerce object to a column name"""

    if isinstance(obj, str):
        return obj
    elif isinstance(obj, F):
        print(obj, obj.__dict__)
        raise ValueError("invalid column object: %s" % obj)
    return obj.name


def split_batch(seq, size, batches):
    start = 0
    it = iter(seq)
    for _ in range(batches):
        yield from itertools.islice(it, start, start + size)
        start += size
