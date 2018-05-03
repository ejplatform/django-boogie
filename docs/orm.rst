=================
Boogie query sets
=================

Django's ORM greatly favors using the active record pattern (access a row at a time,
wrapped into a Python object). We believe it is often a poor abstraction for
using databases and can often lead to inefficient usage patterns and poor architecture.
Boogie implements a few extensions to default Django's query set in order to favor
a more data-driven usage.

Fancy slicing API
=================

Boogie managers and querysets implements a fancy indexing interface inspired
by the Pydata APIs (numpy, pandas, etc). In Boogie, we want to see a model as a
2D table of elements instead of the collection of objects favored by Django
and object oriented interfaces in general.

By doing so, we loose some encapsulation, but on the other hand, it avoids a
host of potential problems such as race conditions, ineffective usage patterns,
coupling of business logic with storage, and often unnecessarily verbose APIs.

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
    from boogie.models import F


Now we create a few users, saving them on the database.

.. code-block:: python

    john   = User.objects.create(name='John Lennon', age=25, pk=0)
    paul   = User.objects.create(name='Paul McCartney', age=26, pk=1)
    george = User.objects.create(name='George Harrison', age=22, pk=2)
    ringo  = User.objects.create(name='Ringo Star', age=29, pk=3)

If you are familiar with Pandas, Boogie API is highly inspired by the .loc
attribute of a Pandas data frame (which in its turn is similar to
fancy indexing in 2D numpy arrays). The metaphor is that a Django manager or queryset
represents a 2D table of values: each row is one specific object and each column corresponds
to a field. Fancy indexing allow us to select parts of this table using
expressive expressions with advanced Python indexing.

Let us start with the simple bits. Each cell is indexed by a row and a column. We can
fetch the content of a single cell by doing so:

>>> users = User.objects
>>> users[0, 'name']
'John Lennon'

Of course we can also use an assignment statement to save/modify values in the
database

>>> users[0, 'name'] = 'John Winston Lennon'

This prevents an useless instantiation of an User object, and the overhead
of calling its .save() method to hit the database. Notice this
operation is carried exclusively at the database level, and any custom logic
implemented in the .save() method will **not** be executed. In fact, we strongly
discourage putting complex logic in .save(), or putting logic in the
model at all.

Boogie only activates when users use 2d indexing. This is a deliberate decision to
preserve compatibility with the slicing syntax of Django query sets. Thus, in order
to fetch a single row from the table we have to use the notation:

>>> users[0, :]
<User: John Winston Lennon>

The scalar 2D access is very limited and we often want to access a group of fields
of an specific row all at once. Fancy indexing comes to rescue:

>>> users[0, ['name', 'age']]
Row('John Winston Lennon', 25)

Assignment is also supported:

>>> users[0, ['name', 'age']] = 'John Lennon', 27

In all those examples, we are interested only on a single object/row in the
database. Boogie also accepts multiple row selectors. If we need, for instance,
to extract a single row from the database, just use the standard Python
syntax for selecting "all elements" slices:

>>> users[:, 'name']
<QuerySet ['John Lennon', 'Paul McCartney', 'George Harrison', 'Ringo Star']>

This call is basically Django's ``users.values_list('name', flat=True). If you
are interested in specific columns, just use

>>> users[:, ['name', 'age']]                                  # doctest: +ELLIPSIS
<QuerySet [Row('John Lennon', 27), Row('Paul McCartney', 26), ...]>

This method returns a sequence of lists representing the selected fields from
each object. In fact, each element behaves as a mutable namedtuple and data can be
accessed either by position or by attribute name.

The first index may also be a list. If that is the case, it is interpreted as a
sequence of primary keys that selects the desired set of rows:

>>> users[[0, 1], :]
<QuerySet [<User: John Lennon>, <User: Paul McCartney>]>

2D indexing is also accepted in many different combinations.

>>> users[[0, 1, 2], 'age']
<QuerySet [27, 26, 22]>
>>> users[[0, 2], ['age', 'name']]
<QuerySet [Row(27, 'John Lennon'), Row(22, 'George Harrison')]>

Finally, the first index can also be a queryset or a Query object for the same
model.

>>> users[users.filter(age__lt=25), 'name']
<QuerySet ['George Harrison']>

It filters over all objects present in the queryset by filtering over all pk
values selected by the queryset index. This functionality is more useful and
expressive when used in conjunction with Q or F-expressions

>>> users[F.age < 25, 'name']
<QuerySet ['George Harrison']>

F expressions can also be used to specify fields, which might be easier to
read and type than strings

>>> users[F.age < 25, [F.name, F.age]]
<QuerySet [Row('George Harrison', 22)]>



The db object
=============

Boogie exports an object called ``db`` that easily exposes a table-centric view
for all models in your project.

.. ignore-next-block

>>> from boogie import db
>>> db.auth.user[:, 'name']
<QuerySet ['John Lennon', 'Paul McCartney', 'George Harrison', 'Ringo Star']>

It must be used with the ``db.<app_label>.<model_name>`` syntax. Under the hood, the db
object calls django.apps.apps.get_model() for a model and return the default
manager.

We believe that managers and query sets should be the default entry point for accessing
your models. Hence, we want to easily expose the model managers instead of the
model classes itself. Boogie managers also define the .new() to easily instantiate
objects without saving them directly on the database.


Overriding query sets and managers
==================================

Implementing custom managers and querysets in Django is not very convenient. First, the
distinction between both is confusing and in most situations the manager is
generated from the queryset class. Not only that, but managers and querysets must
be defined **before** the model. This is not ideal: if we put the model and the
manager in the same module, the manager must be defined first and thus should sit in
the topmost part of the file, which is the most convenient part to access. Boogie let us
organize both classes in a more natural way:

.. ignore-next-block
.. code-block:: python

    from boogie import models

    class User(models.Model):
        name = models.CharField(max_length=100)
        age = models.IntegerField()


    class UserManager(Manager, model=User):
        @models.manager_method
        def create_teen(self, name, age=18):
            return self.create(name=name, age=age)

        def advance_age(self, by=1):
            self.update(age=F.age + 1)

This arrangement prevents a few common Django anti-patterns:

Implementing table logic as class methods of the model class:
    We should create predictable  interfaces and the "Django way" is to put
    table logic in managers and querysets. Not only that, but class methods
    cannot be called later in a chain like standard queryset methods, which
    may hurt the usability of our APIs.
Creating separate models.py and managers.py:
    Putting all models of an app in a file and all managers in another is a
    poor structure: User and UserManager are much more cohesive than, say,
    User and Group. We should split our modules by concerns and not by
    implementation details such as a common base class.
Manager methods in the queryset:
    Creating separate managers and queryset classes involves a lot of
    boilerplate. The usual approach is to create a QuerySet subclass and
    call its ``.as_manager()`` method to create the corresponding
    Manager. This approach makes very easy to slip some methods that should
    belong exclusively into the manager (e.g., object creation patterns) into
    the queryset. Doing so is not very problematic, but could allow spurious
    API usage such as ``Model.objects.filter(age__lt=18).create(name='John', age=42)``.
    In Boogie we can mark that a method exists only in the Manager by decorating
    it with the :func:`boogie.models.manager_method` decorator.



Pandas integration
==================

Sometimes SQL (or Django's ORM) is simply not powerful enough to perform some
advanced multi-row computations. Boogie query sets integrate with
`Pandas <https://pandas.pydata.org>`, which is a great package to perform data
manipulation in table-like structures. Compared to many hand-written solutions
that iterates over a sequence of objects, Pandas data frames offer simpler APIs
and can be much more computationally efficient.

All Boogie query sets have a "to_dataframe()" and "update_dataframe()"
functions. The first returns a dataframe from queryset data:

>>> users[:, ['name', 'age']].to_dataframe()                # doctest: +ELLIPSIS
               name  age
...
0       John Lennon   27
1    Paul McCartney   26
2   George Harrison   22
3        Ringo Star   29

The second updates the database using data from a pandas dataframe. Dataframe
indexes must correspond to primary keys.

>>> df = users[:, 'age'].to_dataframe()
>>> df['age'] += 1
>>> users.update_dataframe(df)
>>> users[0, ['name', 'age']]
Row('John Lennon', 28)
