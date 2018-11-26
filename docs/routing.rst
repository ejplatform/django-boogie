=====================
Url routing and views
=====================

Regex-based routing is flexible, powerful, and can express very sophisticated URL
interfaces. It is also usually much more complicated than necessary. The arcane
syntax of regular expressions is notoriously hard to debug and it is easy to
introduce subtle bugs that can have security implications for your website.

Django 1.11 recognized that regular expressions are an overkill for this task
and introduced the path_ element. Boogie goes one step further and creates
a router object that is responsible for defining urlpatterns through decorators
to view functions in a way that resembles other micro-frameworks such as Flask_
and Bottle_.

.. _path: https://docs.djangoproject.com/en/2.0/ref/urls/#path
.. _Flask: http://flask.pocoo.org/
.. _Bottle: https://bottlepy.org/docs/dev/


Routers
=======

In a Boogie app, we can merge the separate views.py and urls.py and define a
single routes.py module that takes care of both defining the view functions
and associating them to urls. A routes.py module can be defined as bellow:

.. code-block:: python

    # app routes.py
    from boogie.router import Router

    urlpatterns = Router()

    @urlpatterns.route()
    def list(request):
        return render(...)

    @urlpatterns.route('<pk>/')
    def detail(request, pk):
        return render(...)


Each router is declared with the .route() decorator method of a router instance.
Here we also named the router "urlpatterns" in order to make the module
directly included in the global url conf.

.. ignore-next-block
.. code-block:: python

    # urls.py
    from django.urls import path, include

    urlpatterns = [
        (...),
        path('sub-url/', include('my_app.routes')),
    ]

Internally, every view function decorated with the .route() method creates a
new Route object that manages the relationship between view functions and a url.
Route objects are powerful can greatly simplify the task of creating a
view function. First, it can apply a series of transformations in the view
function (that are usually managed by decorators scattered across different
django modules). The example bellow declares a route that requires logged in
users:

.. code-block:: python

    @urlpatterns.route('profile/', login=True)
    def profile_detail(request):
        return (...)

Here is list with all options:

login (bool):
    Redirects the user to login page if not logged in.
staff (bool):
    Only staff members can access the page. Return 404 otherwise.
perms (list):
    A list of permission or a single permission string. Describes the
    permissions necessary to access the page. Return 404 otherwise.
cache:
    Can be False, to disable cache in the page or a dictionary of cache control
    parameters (e.g.: ``{}``)
gzip (bool):
    If true, enable gzip compression for the view.
xframe:
    ``False`` to disable X-Frame clickjacking_ protection; It can also be
    ``'deny'`` and ``'sameorigin'`` to set the appropriate X-Frame protection
    policy.
csrf:
    Can be True or False to enable/disable Django's CSRF_ protection.
    Alternatively, it can be 'token' to include the CSRF token in the request,
    but not reject requests. It can also be 'cookie' to ensure that the cookie
    was sent.
decorators:
    A list of decorator functions to be applied to the view just before the
    previous transformations.

.. _clickjacking: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options#Browser_compatibility
.. _CSRF: https://docs.djangoproject.com/en/2.0/ref/csrf/


Boogie view functions
---------------------

Django view functions must comply with a very simple contract: they receive
a request + url params and return an HttpsResponse instance. While elegant, this
approach has a series of practical problems.

Django's approach hinders testability:

Django-boogie url router translates nice url template expressions to low-level
regexes that Django understands.

