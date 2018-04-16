=====================
Url routing and views
=====================

(Work in progress)


Regex-based routing is flexible, powerful, and can express very sophisticated URL
interfaces. It is also usually much more complicated than necessary. The arcane
syntax is notoriously hard to debug and it is easy to introduce subtle bugs that
can have security implications for your website.

Django 1.11 recognized that regular expressions are an overkill for this task
and introduced the `path` element. Boogie expands on this syntax and creates
a router object that is responsible for defining the regular expressions of an
application through decorators. Boogie exposes an unified framework for
declaring view functions associated with specific routes. The API is inspired by
Flask and Sinatra microframeworks and generally leads to less boilerplate and can
simplify the view functions when compared with the standard Django way.

Boogie view functions
=====================

Django view functions receive request objects, a few parameters and return
the corresponding responses. While elegant, this approach has a series of
practical problems. Complexity of view functions can quickly escalate
if an endpoint require different behaviors for distinct HTTP methods,
headers, parameters, and application states.

Django's approach also lacks testability: ...

Django-boogie url router translates nice url template expressions to low-level
regexes that Django understands.

.. code-block:: python

    from boogie import Router

    route = Router()

    @route('user/<slug:user>/')
    def user_detail(user: User):
        """
        Prints user detail.
        """
        return '<p>Hello %s!</p>' % user.get_full_name()


    urlpatterns = [
        include(route.patterns),
    ]


Boogie "PHP" mode
=================

PHP is certainly not a language we want to draw much inspiration from. However, we recognize
that PHP has a great appeal due to the easy deploys of the LAMP stack during the
early 2000's. Put a PHP file somewhere in your server it is magically live. This kind of
simplicity is worth reproducing.

We don't want to repeat this exact experience because of the host of problems
it creates. However, some of this simplicity can be reproduced in Django in a
sane and secure way.

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