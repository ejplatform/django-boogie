.. image:: https://travis-ci.org/fabiommendes/django-boogie.svg?branch=master
    :target: https://travis-ci.org/fabiommendes/django-boogie/

.. image:: https://coveralls.io/repos/github/fabiommendes/django-boogie/badge.svg?branch=master
    :target: https://coveralls.io/github/fabiommendes/django-boogie?branch=master


Django is nice and powerful, but sometimes it feels too serious. Django-boogie
brings some cool ideas from other libraries and frameworks to Django in order to
make development easier and more effective.

Django-boogie provides:

* A improved F object that allows for more idiomatic query expressions.
* A new url mapper that do not rely on regular expressions.
* A unified manager/queryset class that exposes itself as a table data
  structure with an API inspired in the PyData stack (numpy, pandas and friends).
* A system of hooks that allows greater interoperability and extensibility
  between different apps.


Installation instructions
=========================

Django Boogie can be installed using pip::

    $ python3 -m pip install django-boogie

Or better yet, add it to your requirements.txt or setup.py. After installing
with pip, you'll probably want to add ``'boogie'`` to your ``INSTALLED_APPS``.
