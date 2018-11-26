=====
Ideas
=====


Boogie "PHP" mode
=================

PHP is not a language we want to draw much inspiration from. However, we recognize
that PHP has a great appeal due to the easy deploys of the LAMP stack during the
early 2000's. Put a PHP file somewhere in your server and it is magically live.
This kind of simplicity is worth reproducing.

We cannot repeat this exact experience because of the host of technical
difficulties in integrating a Django project into a CGI-like mindset. However,
some good parts of this experience can be reproduced in Django in a sane and
secure way.

::

    pages/
      |- index.jinja2
      \- user/
           |- urls.yml
           |- index.jinja2
           |- detail.jinja2
           \- profile.jinja2

.. code-block:: yaml

    # urls.yml
    detail:
        url: "/<slug:user.username>/"
        user: auth.user
    profile:
        view: auth.profile_view



Proxy factories
===============



Proxy factories
---------------

Proxy objects to solve a very simple problem: how can we attach additional
properties to arbitrary objects that come exclusively from

.. ignore-next-block
>>> github_link = lambda x: 'http://github.com/' + x.account + '/'
>>> user = proxy(user, is_hacker=True, account='torvalds', link=github_link)
>>> user.link
'http://github.com/torvalds/'

If called without the first argument, it becomes a proxy factory:

.. ignore-next-block
>>> git_user = proxy(is_hacker=lambda x: x.username == 'torvalds', link=github_link)
>>> wrapped = git_user(linus)
>>> wrapped.is_hacker
True


Proxy understand rules and values:

.. ignore-next-block
>>> proxy(rules={'is_ok'}, perms={'can_view': 'foo.can_view'}, values={})

Similarly to proxy, we can have proxy_collection. It augments the elements of a
collection rather than the collection itself. It supports query sets, dicts,
and sequences and iterables.


Job runner
==========

Celery is a great task runner and takes care of many issues inherent to running
asynchronous tasks in distributed systems.


.. ignore-next-block
.. code-block:: python

    @job()
    def process_data(object: Foo, n_iter=100):
        ...



    process_data.create()



Invoke tasks
============

Django API for creating management commands is clumsy, verbose and absolutely
inconvenient. We have first to create a "management" package inside our app with
a "commands" sub-package inside it. Each module inside "commands" implements
one different command that should inherit from ``from django.core.management.base import BaseCommand``::

    app/
      |- management/
      |    |- commands/
      |    |    |- __init__.py
      |    |    |- thiscommandshouldbetterworthit.py
      |    |    \- anothercommandmodule.py
      |    \- __init__.py
      |- models.py
      |- ...
      \- routes.py

.. code-block:: python

    # thiscommandshouldbetterworthit.py

    from django.core.management.base import BaseCommand

    class Command(BaseCommand):
        help = 'A simple command'

        def add_arguments(self, parser):
            # Oh my :(
            parser.add_argument(
                '--argument',
                action='store_true',
                help='Forces you to go to the documentation of argparse to '
                     'discover the argument parameters',
            )

        def handle(self, *args, silent=False, **options):
            now_we_can_do_something_useful()


Compare this unacceptable cruft with more modern Python approaches such as Invoke_:

.. code-block:: python

    from invoke import task

    @task
    def my_command(ctx, argument=None, flag=False):
        do_something_useful()


.. _Invoke: http://www.pyinvoke.org/


Invoke task are better to write and better to execute, compare::

    $ python manage.py cmd
    vs.
    $ inv cmd

    Ah! it can also be chained
    $ inv cmd1 --flag1 cmd2 cmd3

Boogie exposes management commands as Invoke tasks in the Django namespace so
you can mostly abandon the Django manage.py nonsense and work with a proper
task management solution. Boogie also exposes a few useful reusable tasks that
you can import into your project and provides an infrastructure for apps to
export discoverable tasks easily accessible from the global tasks.py file.


Using Django management commands
================================

...

Boogie invocations
==================

...

Per-app tasks
=============

...


Exporting tasks back to Django
==============================

...


