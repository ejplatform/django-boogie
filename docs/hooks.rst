=====
Hooks
=====

The `boogie.hooks` module defines simple hooks that allow third parties to
extend your code without ever changing it. This kind of inversion of dependency
allows for very flexible code and can help with interoperability and consistency
between different modules.


App initialization hooks
========================


Advanced hooks
==============

Base class injection
--------------------

Implements a hook that allows one to register additional base classes prior to
its creation. This mechanism can be used, for instance, to inject additional
fields to a model without ever touching its code or creating an auxiliary
sub-class that uses the non-ideal multi-table inheritance. You should exercise
some caution and it is highly recommended to only inject fields that either
define a default or are nullable.

The model must be extensible, which is accomplished by using the
:func:`extensible` function in the following way:

.. ignore-next-block
.. code-block:: python

    # We define in users/models.py

    from boogie.hooks import extensible

    class User(*extensible('users.User', models.Model)):
        "An extensible user model."


    # In another file that is loaded before users/models.py...

    from boogie.hooks import base_of

    @base_of('users.User')
    class UserExt(models.Model):
        "Adds a github page value to the user"

        class Meta:
            abstract = True

        github_page = models.UrlField()


Now the user model has a github_page value defined by a third party.


Declare common arguments
------------------------

Many times in code, specially during value declarations, we have to choose
some values in an arbitrary fashion that cannot be changed by users of our
models. That "description" CharField should have a ``max_length`` of 100 or 140?
The user of our model has no control of it, and you as a developer must keep
track of many parameters such as ``max_length``, ``help_text``, etc for various
related fields in order to make your models behave in a consistent way.

This hook allows us to share a set of parameters between value declarations.
First we create a params object with an unique identification and a set of
default values for this param:

.. ignore-next-block
.. code-block:: python

    from boogie.hooks import set_params

    name_params = set_params(
        'user.name',
        max_length=100,
        verbose_name=_('name'),
    )

Values can also be declared in settings.py as bellow

.. ignore-next-block
.. code-block:: python

    # settings.py

    DEFAULT_PARAMS = {
        'user.name': {
            'max_length': 100,
            'verbose_name': _('name'),
        },
        'foo.bar': {
            'help_text': _('foos a bar'),
            'verbose_name': _('foobar'),
            'blank': True,
        },
    }

In a different module, we either import this params object or load it from a
global registry. We will illustrate the second option:

.. ignore-next-block
.. code-block:: python

    from boogie.hooks import get_params

    name_params = get_params('user.name', max_length=200)

    class User(models.Model):
        name = CharField(**name_params)
        mothers_name = CharField(**name_params(blank=True))


Notice that get_params not only load the param object, but we could also define
additional arguments. This can be a little confusing, but there are simple rules
that make those functions work together:

* ``set_params`` always overrides the current value of a parameter. If you call
  it twice for the same id, it will update the values assigned to it.
* ``get_params`` extra arguments only define safe default values for the params
  object it returns. Those values are used *only if* not defined elsewhere.
* users can configure the values in settings.py. This has a higher priority than
  values declared with set_params.
* when a params object is called, it returns a dictionary of all defined params.
  if you pass extra keyword arguments, like in the second char value in the
  example, those values have the highest priority and are passed to the mapping.
