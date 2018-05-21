=================
boogie.apps.users
=================

Boogie Users is a simple app that provides a User model similar to
"django.contrib.auth" user. The only difference is that it does not use separate
"first_name" and "last_name" fields, but rather join both fields into a single
"name" field.

Naming patterns vary widely in different parts of the world and the "first_name",
"last_name" convention, while common in the US and some part of Europe is too
restrictive for most of the world. We adopt a single "name" field for greater
flexibility.

Usage
=====

Add "boogie.apps.users" to your INSTALLED_APPS and set AUTH_USER_MODEL to
"users.User":

.. code-block:: python

    INSTALLED_APPS = [
        ...,
        'boogie.apps.users',
        'django.contrib.auth',
        ...,
    ]

    AUTH_USER_MODEL = 'users.User'


Abstract model
==============

Boogie users also provides an abstract version in case you need to personalize
the default User model. If that is the case, simply import the abstract model
and register your model in AUTH_USER_MODEL setting:

.. code-block:: python

    # On your own app models.py
    from boogie.apps.users.models import AbstractUser

    class MyUserModel(AbstractUser):
        # extra fields
        ...

        # extra props
        @property
        def has_university_account(self):
            return self.email.endswith('@some-university.com')


    # settings.py
    ...
    AUTH_USER_MODEL = 'my_accounts.MyUserModel'


There is no need (and it is a bad practice) to include "boogie.apps.users" in
your INSTALLED_APPS if you just want to use the abstract model.