import collections
from functools import lru_cache, partial

from bulk_update.helper import bulk_update
from django.db import models
from django.db.models.query import ValuesListIterable
from django_pandas.managers import DataFrameQuerySet
from manager_utils import ManagerUtilsQuerySet

from sidekick import lazy, itertools
from .expressions import F
from ..utils.linear_namespace import linear_namespace

F_EXPR_TYPE = type(F.age > 0)


class QuerySet(ManagerUtilsQuerySet, DataFrameQuerySet):
    """
    Boogie's drop in replacement to Django's query sets.

    It extends the query set API with a Pydata-inspired interface to select data
    """

    # Properties
    index = property(lambda self: Index(self))
    __column_names = None
    __is_column_slice = False

    # Class methods
    def as_manager(cls):
        # Overrides to use Boogie manager instead of the default manager

        from .manager import Manager
        manager = Manager.from_queryset(cls)()
        manager._built_with_as_manager = True
        return manager

    as_manager.queryset_only = True
    as_manager = classmethod(as_manager)

    def __getitem__(self, item):
        # 1D indexing is basic delegated to Django. We extend it with some
        # idioms that preserve backwards compatilibity
        if not isinstance(item, tuple):
            return getitem_1d(self, item)

        try:
            row, col = item
        except IndexError:
            raise TypeError('only 1d or 2d indexing is allowed')

        return getitem_2d(self, row, col)

    def __setitem__(self, item, value):
        # Similarly to getitem, we dispatch for the 1d and 2d indexing
        # functions
        if not isinstance(item, tuple):
            return setitem_1d(self, item, value)

        try:
            row, col = item
        except IndexError:
            raise TypeError('only 1d or 2d indexing is allowed')

        return setitem_2d(self, row, col, value)

    # Better accessors
    def update_item(self, pk, **kwargs):
        """
        Updates a single item in the queryset.
        """
        return self.filter(pk=pk).update(**kwargs)

    update_item.alters_data = True

    def bulk_update(self, objects, fields=None, exclude=None, batch_size=None,
                    using='default', pk_field='pk'):
        """
        Update all objects in the given list. Optionally, a list of fields to
        be updated can also be passed.

        Args:
            objects (sequence):
                List of model instances.
            fields:
                Optional lists of names to be found.
            batch_size (int):
                Maximum size of each batch sent for update.
        """
        bulk_update(objects, meta=self.model._meta,
                    update_fields=fields, exclude_fields=exclude,
                    using=using, batch_size=batch_size, pk_field=pk_field)

    bulk_update.alters_data = True

    #
    # Enhanced API
    #
    def select_columns(self, *fields):
        """
        Similar to .values_list(*fields)
        """
        return select_columns(self, list(fields))

    def values(self, *fields, **expressions):
        qs = super().values(*fields, **expressions)
        fields = fields + tuple(expressions.keys())
        return self._mark_column_names(fields, qs)

    def values_list(self, *fields, **kwargs):
        qs = super().values_list(*fields, **kwargs)
        return self._mark_column_names(fields, qs)

    def _mark_column_names(self, columns, qs=None):
        qs = self if qs is None else qs
        qs.__is_column_slice = True
        qs.__column_names = columns
        return qs

    #
    # Pandas data frame and numpy array APIs
    #
    def to_dataframe(self):
        """
        Convert query set to a Pandas data frame
        """
        import pandas as pd

        if self.__column_names:
            fields = self.__column_names
        else:
            fields = self.model._meta.fields

        # Build data frame
        data = list(self.values_list('pk', *fields))
        df = pd.DataFrame(data, columns=['Index[pk]', *fields])
        df.index = df.pop('Index[pk]')
        df.index.name = 'pk'
        return df

    def update_dataframe(self, dataframe, batch_size=None, in_bulk=True):
        """
        Persist data frame data to the database. Data frame index must
        correspond to primary keys.

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

        for pk, row in zip(dataframe.index, dataframe.to_dict('records')):
            row.setdefault('pk', pk)
            add_object(new_object(**row))

        if in_bulk:
            self.bulk_update(objects,
                             fields=list(fields),
                             batch_size=batch_size)
        else:
            for obj in objects:
                obj.save(update_fields=fields)

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
# Auxiliary classes
# ----------------------------------------------------------------------------
class QuerysetSequence(collections.Sequence):
    """
    Base class for sequences tyeps fed by query sets instances.
    """

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
        return '%s(%s)' % (type(self).__name__, list(self))


class Index(QuerysetSequence):
    """
    Returns an index with the primary keys of all elements.
    """

    @staticmethod
    def prepare(qs):
        return qs.values_list('pk', flat=True)


class RowIterable(ValuesListIterable):
    """
    Iterable returned by QuerySet.values_list(named=True) that yields a
    namedtuple for each row.
    """

    @staticmethod
    @lru_cache()
    def _create_row_class(names):
        return linear_namespace('Row', names)

    def __init__(self, *args, **kwargs):
        self.field_names = kwargs.pop('field_names', None)
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


#
# Getitem auxiliary functions
# ----------------------------------------------------------------------------
def getitem_1d(qs, item):
    """
    Must dispatch to super() in all situations that Django supports:

    We keep Django's behavior in all of the following cases (a, b >= 0):
    * qs[a]
    * qs[a:b]

    Small extensions:
    * qs[-a] -> fetch from last
    * qs[a, -b] -> specify a index from first to last

    Larger extensions:
    * qs[list] -> ...
    """

    # Integer indexes
    if isinstance(item, int):
        if item >= 0:
            return super(QuerySet, qs).__getitem__(item)
        else:
            idx = -item - 1
            return qs.reverse()[idx] if qs.ordered else qs.order_by('-id')[idx]

    # Slicing
    if isinstance(item, slice):
        start, stop, step = item.start, item.stop, item.step
        if step is None and \
                (start is None or start >= 0) and \
                (stop is None or stop >= 0):
            return super(QuerySet, qs).__getitem__(item)

    raise TypeError('invalid index type: %r' % item.__class__.__name__)


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
        raise IndexError('invalid column slice: %s' % rows)

    elif isinstance(rows, QuerySet):
        return qs & rows

    elif isinstance(rows, F_EXPR_TYPE):
        return qs.filter(rows)

    raise TypeError('invalid row selector: %r' % rows.__class__.__name__)


def select_columns(qs, cols):
    if isinstance(cols, list):
        qs = qs.values_list(*cols, flat=False)
        field_names = get_column_names(cols, qs)
        qs._iterable_class = partial(RowIterable, field_names=field_names)
        return qs

    elif isinstance(cols, slice):
        if cols == slice(None, None, None):
            return qs
        raise IndexError('invalid column slice: %s' % cols)

    elif isinstance(cols, (str, F, models.F)):
        return qs.values_list(cols, flat=True)

    raise TypeError('invalid column selector: %r' % cols.__class__.__name__)


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
            raise TypeError('invalid column', col)
        append(name)
    return names


#
# Setitem auxiliary functions
# ----------------------------------------------------------------------------
def setitem_1d(qs, item, value):
    raise TypeError('invalid index type: %r' % item.__class__.__name__)


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
    raise TypeError('invalid column selector: %r' % cols.__class__.__name__)


def as_col_name(obj):
    "Coerce object to a column name"

    if isinstance(obj, str):
        return obj
    elif isinstance(obj, F):
        print(obj, obj.__dict__)
        raise ValueError('invalid column object: %s' % obj)
    return obj.name


def split_batch(seq, size, batches):
    start = 0
    it = iter(seq)
    for _ in range(batches):
        yield from itertools.islice(it, start, start + size)
        start += size
