=================
Boogie query sets
=================

Django's ORM favors using the active record pattern (access a row at a time,
wrapped into a Python object). We believe it is often a poor abstraction for
using databases and can often lead to inefficient usage patterns and a poor
architecture. Boogie implements a few extensions to default Django's query set
and managers APIs in order to favor more data-driven approaches.

Fancy slicing API
=================

Boogie managers and querysets implements a fancy indexing interface inspired
on Numpy and Pandas. In Boogie, we want to see the database as a 2D table of
scalars instead of a collection of complex objects as is implied by the ORM.

By doing so, we loose some encapsulation, but on the other hand, it avoids a
host of potential problems such as race conditions, ineffective usage patterns
(specially, the N + 1 problem), coupling of business logic with storage, and
doing so we often avoid some unnecessarily verbose APIs.

In order to illustrate fancy indexing in Boogie, let us start constructing a
small group of elements. First the model:

.. ignore-next-block
.. code-block:: python
    # models.py

    from django.db import models

    class User(models.Model):
        name = models.CharField(max_length=100)
        age = models.IntegerField()

.. invisible-code-block:: python

    from tests.testapp.models import User
    from boogie.models import Q, F


Now we create a few users, saving them on the database.

.. code-block:: python

    john   = User.objects.create(name='John Lennon', age=25, pk=1)
    paul   = User.objects.create(name='Paul McCartney', age=26, pk=2)
    george = User.objects.create(name='George Harrison', age=22, pk=3)
    ringo  = User.objects.create(name='Ringo Star', age=29, pk=4)

If you are familiar with Pandas, Boogie API is highly inspired by the .loc
attribute of a Pandas data frame (which in its turn is similar to
fancy indexing in 2D numpy arrays). The metaphor is that a Django manager or queryset
represents a 2D table of values: each row corresponds to an object and each
column corresponds to a field. Fancy indexing allow us to select parts of this
table in ways that avoid instantiating lots of different objects.

Let us start with the simple bits. Each cell is indexed by a row and a column. We can
fetch the content of a single cell like so:

>>> pk = 1
>>> User.objects[pk, 'name']
'John Lennon'

Of course we can also use an assignment statement to save/modify values in the
database

>>> users = User.objects              # A simple trick to save a few key strokes
>>> users[pk, 'name'] = 'John Winston Lennon'

This prevents an unnecessary instantiation of an User object, and the overhead
of calling its .save() method to hit the database. Notice this
operation is carried exclusively at the database level, and any custom logic
implemented in the .save() method will **not** be executed. In fact, we strongly
discourage putting complex logic on .save(), or putting business logic in the
model at all.

Boogie only activates when users use 2d indexing. This is a deliberate decision to
preserve compatibility with the slicing syntax of Django query sets. Thus, in order
to fetch a single row from the table we have to use the notation:

>>> users[pk, :]
<User: John Winston Lennon>

.. warning::
2D indices are interpreted as [rows (by pk), columns (by name)]. This is
    **different** from Django semantics for queryset indices, which are
    interpreted as the positions associated to each item a set of objects.

    Thus ``users.all()[0]`` returns the first element of ``users.all()``,
    while ``users[0, :]`` returns the element with pk=0.

The scalar 2D access is very limited and we often want to access a group of fields
of an specific row all at once. Fancy indexing comes to rescue:

>>> users[pk, ['name', 'age']]
Row('John Winston Lennon', 25)

Assignment is also supported:

>>> users[pk, ['name', 'age']] = 'John Lennon', 27

In all those examples, we are interested only on a single object/row in the
database. Boogie also accepts selectors for multiple rows. Let us extract a
single row from the database: for that, just use the standard Python
syntax for selecting "all elements" in the row index:

>>> users[:, 'name']
<QuerySet ['John Lennon', 'Paul McCartney', 'George Harrison', 'Ringo Star']>

This call is basically an alias to Django's ``users.values_list('name', flat=True).
If you are interested on more than one column, just use

>>> users[:, ['name', 'age']]                                  # doctest: +ELLIPSIS
<QuerySet [Row('John Lennon', 27), Row('Paul McCartney', 26), ...]>

This method returns a sequence of lists representing the selected fields from
each object. In fact, each element behaves as a mutable namedtuple and data can be
accessed either by position or by attribute name.

The first index may also be a list. If that is the case, it is interpreted as a
sequence of primary keys that selects the desired set of rows:

>>> users[[1, 2], :]
<QuerySet [<User: John Lennon>, <User: Paul McCartney>]>

2D indexing is also accepted in many different combinations.

>>> users[[1, 2, 3], 'age']
<QuerySet [27, 26, 22]>
>>> users[[1, 3], ['age', 'name']]
<QuerySet [Row(27, 'John Lennon'), Row(22, 'George Harrison')]>

Finally, the first index can also be a queryset or a Query expression

>>> users[users.filter(age__lt=25), 'name']
<QuerySet ['George Harrison']>

This functionality is more useful and expressive when used in conjunction with
Q or F-expressions:

>>> from boogie.models import F, Q
>>> users[F.age < 25, 'name']
<QuerySet ['George Harrison']>

and this also works...

>>> users[Q(age__lt=25), 'name']
<QuerySet ['George Harrison']>


F expressions can also be used to specify fields. You may find it easier to
read and type than strings

>>> users[F.age < 25, [F.name, F.age]]
<QuerySet [Row('George Harrison', 22)]>



The db object
=============

Boogie exports an object called ``db`` that easily exposes a table-centric view
for all models in your project.

.. ignore-next-block

>>> from boogie import db
>>> db.auth.user_model[:, 'name']
<QuerySet ['John Lennon', 'Paul McCartney', 'George Harrison', 'Ringo Star']>

It must be used with the ``db.<app_label>.<model_name>`` syntax. Under the hood, the db
object calls django.apps.apps.get_model() for a model and return the default
manager.

We believe that managers and query sets should be the default entry point for accessing
your models. Hence, we want to easily expose the model managers instead of the
model classes themselves. Boogie managers also define the .new() method as an
alias to the model constructor.


Overriding query sets and managers
==================================

Implementing custom managers and querysets in Django is greatly convenient.
First, the distinction between both is confusing and in most situations the manager is
generated from the queryset class via a boilerplate. Not only that, but managers
and querysets must be defined **before** the model, since we need to set the
``objects`` during class definition. This is not ideal: it is natural to expect
that models should be in the topmost part of the file (and hence more convenient
to browser). Models declare the structure of tables in the database, and we have
almost no chance of understanding the manager methods before peeking at the model
first. Boogie let us organize both classes in a more natural way:

.. ignore-next-block
.. code-block:: python

    from boogie import models
    from boogie.models import F


    class User(models.Model):
        name = models.CharField(max_length=100)
        age = models.IntegerField()


    #
    # Manager and queryset methods
    #
    @models.manager_method(User)
    def create_teen(self, name, age=18):
        return self.create(name=name, age=age)


    @models.queryset_method(User)
    def advance_age(self, by=1):
        self.update(age=F.age + 1)

This arrangement prevents a few common Django anti-patterns:

Implementing table logic as class methods of the model class:
    We should create predictable  interfaces and the "Django way" is to put
    table logic in managers and querysets. Not only that, but class methods
    cannot be called later in a chain like standard queryset methods, which
    hurts the usability of our APIs.
Creating separate models.py and managers.py:
    Putting all models of an app in a file and all managers in another is a
    poor structure: User and UserQuerySet are much more cohesive than, say,
    User and Group. We should split our modules by concerns and not by
    implementation details such as a common base class.
Manager methods in the queryset:
    Creating separate managers and queryset classes involves a lot of
    boilerplate. The usual approach is to create a QuerySet subclass and
    call ``Manager.from_queryset()`` to create the corresponding
    Manager class. This approach makes it very tempting to move some methods
    that should belong exclusively into the manager (e.g., object creation patterns)
    to queryset to avoid an extra class declaration. Doing so is not very
    problematic, but would allow some spurious API usage such as
    ``obj = Model.objects.filter(age__lt=18).my_create_method(name='John', age=42)``.
    In Boogie we can mark that a method exists only in the Manager by decorating
    it with the :func:`boogie.models.manager_only` decorator.



Pandas integration
==================

Sometimes SQL (or Django's ORM) is simply not powerful enough to perform some
advanced multi-row computations. Boogie query sets integrate with
`Pandas <https://pandas.pydata.org>`, which is a great package to perform data
manipulation in table-like structures. Compared to many hand-written solutions
that iterates over a sequence of objects, Pandas data frames offer simple APIs
and can be much more computationally efficient than ad hoc python solutions.

All Boogie query sets have both a "dataframe()" and a "update_from_dataframe()"
methods. The first returns a dataframe from queryset data:

>>> users[:, ['name', 'age']].dataframe()       # doctest: +NORMALIZE_WHITESPACE
               name  age
id
1       John Lennon   27
2    Paul McCartney   26
3   George Harrison   22
4        Ringo Star   29

The second updates the database using data from a pandas dataframe. Dataframe
indexes must correspond to primary keys.

>>> df = users[:, 'age'].dataframe()
>>> df['age'] += 1
>>> users.update_from_dataframe(df)
>>> users[:, ['name', 'age']].dataframe()       # doctest: +NORMALIZE_WHITESPACE
               name  age
id
1       John Lennon   28
2    Paul McCartney   27
3   George Harrison   23
4        Ringo Star   30


Alternate Meta syntax and integration with model-utils and django-polymorphic
=============================================================================

Django introduced the Meta syntax before Python 3 even existed and at that time
it wasn't possible to pass keyword arguments to class constructors. We believe
that the second would be a more natural idiom in modern Python, but obviously
Django cannot break this interface for backwards compatibility.

In Boogie, the ``Meta`` information can be passed either in the traditional way
using the ``class Meta: ...`` convention or as keyword arguments in the model
declaration:

.. code-block:: python

    from boogie import models


    class BaseUser(models.Model, abstract=True, status=True):
        name = models.CharField(max_length=100)
        age = models.IntegerField()


Besides all the usual`Meta options`_, Boogie also allows some custom model
initialization that integrates with external libraries to provide additional
functionality to your models:

timeframed (bool):
    Makes model a subclass of Django Model Utils TimeFramedModel_. Adds ``start``
    and ``end`` nullable DateTimeFields, and a ``timeframed`` manager that
    returns only objects for whom the current date-time lies within their time range.
timestamped (bool):
    Makes model a subclass of Django Model Utils TimeStampedModel_. Provides
    self-updating ``created`` and ``modified`` fields on any model that inherits from it.
status (bool):
    Makes model a subclass of Django Model Utils StatusModel_. Provides ``status``
    and ``status_changed`` fields that control the current status of an instance
    based on a list of choices. See the documentation for more details.
soft_deletable (bool):
    Makes model a subclass of Django Model Utils SoftDeletableModel_. Provides
    field ``is_removed`` which is set to ``True`` instead of removing the
    instance when schedule for deletion. Entities returned in default manager
    are limited to not-deleted instances.
polymorphic (bool):
    Makes model a subclass of PolymorphicModel_, which adds an additional
    column ``ctype`` that tracks the actual type of each instance in a multiple
    table inheritance scenario.

.. _Meta options: https://docs.djangoproject.com/en/2.1/ref/models/options/
.. _TimeFramedModel: https://django-model-utils.readthedocs.io/en/latest/models.html#timeframedmodel
.. _TimeStampedModel: https://django-model-utils.readthedocs.io/en/latest/models.html#timestampedmodel
.. _StatusModel: https://django-model-utils.readthedocs.io/en/latest/models.html#statusmodel
.. _SoftDeletableModel: https://django-model-utils.readthedocs.io/en/latest/models.html#softdeletablemodel
.. _PolymorphicModel: https://django-polymorphic.readthedocs.io/en/stable/quickstart.html#making-your-models-polymorphic