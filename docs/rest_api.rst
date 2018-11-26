.. module:: boogie.rest

===================
Automatic Rest APIs
===================

Django Rest Framework (DRF) is very powerful and flexible, but it also requires
a lot of boilerplate to declare even simple APIs. This is aggravated if we
want to build a truly RESTful API with HATEAOS controls (also known as a level
3 API according to `Richardson maturity model`_). This is how REST is supposed to
work and, while DRF allow us to do this, it is not the easier path. In Boogie,
creating a RESTful API can be as simple as adding a few decorators
to your model declarations.

.. _Richardson maturity model: https://martinfowler.com/articles/richardsonMaturityModel.html

.. ignore-next-block
.. code-block:: python

    from django.db import models
    from boogie.rest import rest_api

    @rest_api()
    class Book(models.Model):
        author = models.ForeignKey('Author', on_delete=models.CASCADE)
        publisher = models.ForeignKey('Publisher', on_delete=models.CASCADE)
        title = models.TextField()

        def __str__(self):
            return self.title

    @rest_api()
    class Author(models.Model):
        name = models.TextField()

        def __str__(self):
            return self.name

    @rest_api()
    class Publisher(models.Model):
        name = models.TextField()

        def __str__(self):
            return self.name


Now, just add the following line on your project's urls.py:

.. ignore-next-block
.. code-block:: python

    urlpatterns = [
        ...,
        path('api/', include(rest_api.urls)),
    ]

Under the hood, Boogie creates Serializer and ViewSet classes for each
model using Django REST Framework and configure a router that organizes every
end-point declared. Boogie enforces API versioning, so you should point your
browser to "/api/v1/" in order to obtain something like this:


.. code-block:: json

    {
        "books": "https://my-site.com/api/v1/books/",
        "authors": "https://my-site.com/api/v1/authors/",
        "publishers": "https://my-site.com/api/v1/publishers/"
    }

Each resource is then constructed automatically according to the information
passed to the rest_api decorator. In our case, it exposes all fields of each
model and stores foreign relations as hyperlinks under the "links" object:

.. code-block:: json

    {
        "links": {
            "self": "https://my-site.com/api/v1/books/42/",
            "author": "https://my-site.com/api/v1/author/12/",
            "publisher": "https://my-site.com/api/v1/publisher/2/",
        }
        "author": "Malaclypse, The Younger",
        "publisher": "Loompanics Unltd",
        "title": "Principia Discordia"
    }


Extending the default API
=========================

Extra properties and attributes
-------------------------------

We can declare additional attributes using the :func:`rest_api.property`
decorator.


Additional URLs
---------------

By default, Boogie creates two kinds of routes for each resource: one is list-based,
usually under /api/v1/<resource-name>/, and the other is a detail view under
/api/v1/<resource-name>/<id>/. It is possible to create additional URLs
associated with either a single document (detail view) or a queryset (list view).

Those additional urls can be created with the @rest_api.action decorator. We
suggest putting those functions in a ``api.py`` file inside your app.

.. ignore-next-block
.. code-block:: python

    # api.py file inside your app

    from boogie.rest import rest_api

    @rest_api.list_action('books.Book')
    def recommended(request, books):
        """
        List of recommended books for user.
        """
        return books.recommended_for_user(request.user)

    @rest_api.detail_action('books.Book')
    def same_author(book):
        """
        List of authors.
        """
        return book.author.books()


This creates two additional endpoints:

.. code-block:: python

    # /api/v1/books/recommended/
    [
        {
            "links": { ... },
            "author": "Malaclypse, The Younger",
            "publisher": "Loompanics Unltd",
            "title": "Principia Discordia"
        },
        {
            "links": { ... },
            "author": "Robert Anton Wilson",
            "publisher": "Dell Publishing",
            "title": "Illuminatus!"
        }
    ]


    # /api/v1/books/42/same-author/
    [
        {
            "links": { ... },
            "author": "Malaclypse, The Younger",
            "publisher": "Loompanics Unltd",
            "title": "Principia Discordia"
        },
    ]

Boogie tries to be flexible regarding the input and output parameters of action
functions. Generally speaking, everything that can be safely serialized by the
rest_api object can be returned as the output of those functions. See the
:meth:`RestAPI.detail_action` documentation for more details.


Custom viewsets and serializers
-------------------------------

You can also completely override the default Boogie viewsets and serializers and
specify your own classes. The :meth:`RestAPI.register_viewset` method allow us
to completely specify a custom viewset class.


Custom routers
--------------

#TODO

Customizing viewsets and serializers
====================================

Sometimes, the created viewsets and serializers are not good enough to
specify your desired API. Boogie allow us to register completely custom viewset
classes, but most this is an overkill: Boogie provides hooks to register
special methods to be inserted in Boogie serializer and viewset classes classes
so you can still benefit from what Boogie provides by default while having great
flexbility.

Object creation hooks
---------------------

This is common pattern when designing an API: a model have a few hidden fields
that are not exposed, but during object creation, they can be calculated from
the user that makes the request. The most common use case is probably when
we want to add a reference to the user who made the request in an "author" or
"owner" field.

Hooks can be registered using any of the decorators :meth:`RestAPI.save_hook`,
:meth:`RestAPI.delete_hook`.

Example:

.. ignore-next-block
.. code-block:: python

    @rest_api.save_hook(Book)
    def save_book(request, book):
        if book.author is None:
            book.author = request.user.as_author()
        return book


    @rest_api.save_hook(Book)
    def delete_book(request, book):
        if book.can_delete(request.user):
            book.delete()
        else:
            raise PermissionError('user cannot delete book')


Configurations
--------------

Boogie understands the following global configurations in Django settings:

BOOGIE_REST_API_SCHEMA:
    When not given, it uses the same uri schema (e.g., http) as the current
    request object. It is possible to override this behavior to select an
    specific schema such as 'http' or 'https'. This configuration may be necessary
    when Django is running behind a reverse proxy such as Ngnix. Communication with
    the reverse proxy is typically done without encryption, even when the public
    facing site uses https. Setting ``BOOGIE_REST_API_SCHEMA='https'`` makes
    all urls references provided by the API to use https independently of how
    the user accessed the API endpoint.


Mixin hooks
-----------

For maximum flexibility, you can specify an entire mixin class to be included
into the inheritance chain during creation. This advanced feature requires knowledge
of the inner works of DRF and, to some extent, of Boogie serializer
:class:`RestAPISerializer` and viewset :class:`RestAPIBaseViewSet` classes. That
said, mixin classes can be added to the class using the :meth:`RestAPI.serializer_mixin`
and :meth:`RestAPI.viewset_mixin` decorators:


.. ignore-next-block
.. code-block:: python

    @rest_api.viewset_mixin(Book)
    class BookViewSetMixin:
        def create(request):
            if request.user.can_register_book():
                return super().create(request)
            else:
                raise PermissionError('user cannot register book!')




Retrieving viewsets and serializers
===================================

Boogie exposes the serializers, viewsets and router objects created internally
by the rest_api object. They also can be used to directly serialize an object
or queryset or to expose a view function.

The easier way to use Boogie serializers is the invoking :meth:`RestAPI.serialize`
method.


Versions
========

Django Boogie assumes that the API is versioned and can expose different set of
resources and different properties of the same resource. By default, all entry
points are created under the "v1" namespace. Users can register different
fields, properties and actions under different API version names:

.. ignore-next-block
.. code-block:: python

    @rest_api(['author', 'title'], version='v1')
    @rest_api(['title'], version='v2')
    class Book(models.Model):
        author = models.CharField(...)
        title = models.Charfield(...)

Other decorators also accept the version argument. Omitting version means that
the property is applied to all versions of the API. Versions can also be lists,
meaning that the decorator applies the given settings to all versions on the
list.

.. ignore-next-block
.. code-block:: python

    @rest_api.list_action(Book, version=['v1', 'v2'])
    def readers(request):
        return book.readers.all()


API Documentation
=================

The :obj:`rest_api` object is a globally available instance of the
:class:`RestAPI` class.

.. autoclass:: RestAPI
   :members:
