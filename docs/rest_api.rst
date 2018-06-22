.. module:: boogie.rest

===================
Automatic Rest APIs
===================

Django Rest Framework (DRF) is very powerful and flexible, but it also requires
a lot of boilerplate to declare even simple APIs. This is aggravated if we
want to build a truly RESTful API with HATEAOS controls (also known as a level
3 API according to `Richardson maturity model <https://martinfowler.com/articles/richardsonMaturityModel.html>`_).
This is how REST is supposed to work and we should really aim for this kind
architecture if using REST. DRF allow us to do this, but it is not the easier
path. In Boogie, creating a RESTful API can be as simple as adding a few decorators
to your model declarations.

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

By default, Boogie creates two kinds of routes for each resource: one is a list
of resources (usually under /api/v1/<resource-name>/) and the other is a detail
view for each resource (under /api/v1/<resource-name>/<id>/). It is possible to
create additional URLs associated with either a single resource (detail view)
or a queryset (list view).




Custom serializers
------------------

#TODO

Custom viewsets
---------------
#TODO

Custom routers
--------------

#TODO

Using internal serializers
==========================

Boogie exposes the serializers, viewsets and router objects created internally
by the rest_api object. They also can be used to directly serialize an object
or queryset or to expose a view function.

The easier is the :meth:`RestAPI.serialize` method.


API documentation
-----------------

.. automethod:: RestAPI.serialize
.. automethod:: RestAPI.get_serializer
.. automethod:: RestAPI.get_viewset



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
meaning that the decorator applies to all versions on the list.

.. ignore-next-block
.. code-block:: python

    @rest_api.action(Book, version=['v1', 'v2'])
    def readers(request, book):
        return book.readers.all()


API Documentation
=================

.. autoclass:: RestAPI