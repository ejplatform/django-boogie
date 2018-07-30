.. image:: https://travis-ci.org/fabiommendes/django-boogie.svg?branch=master
    :target: https://travis-ci.org/fabiommendes/django-boogie/

.. image:: https://coveralls.io/repos/github/fabiommendes/django-boogie/badge.svg?branch=master
    :target: https://coveralls.io/github/fabiommendes/django-boogie?branch=master


Django-Boogie is a framework formed by several loosely coupled modules that
rethinks some of Django's practices. You can use any part of Boogie you want.

Highlights:

* Class-based settings.
* Easy creation of rest APIs with a simple decorator.
* A Flask inspired router that merges views and urls in a single module.
* A Pandas inspired API for querysets + simple integration with Pandas.
* A improved F object that allows more idiomatic query expressions.
* And more!

Installation instructions
=========================

Django Boogie can be installed using pip::

    $ python3 -m pip install django-boogie

Or better yet, add it to your requirements.txt or setup.py. Boogie does not
need to be added to your ``INSTALLED_APPS``. It requires Django 2.0+ and Python 3.6+.
