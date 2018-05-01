Django Rest Framework (WIP)
===========================

Django Rest Framework (DRF) is very powerful and flexible, but it also requires
a lot of boilerplate to declare even simple APIs. This is aggravated if we
want to build a trully RESTful API with HATEAOS controls (also known as a level
3 API according to ?? maturity model). This is how REST is supposed to work
and we should really aim for this kind organization, however DRF do not make it
the easier route. In Boogie, creating a RESTful API is as simple as adding a
few decorators.


.. code-block:: python

    @rest_api()
    class Book(models.Model):
        author = models.ForeignKey('Author')
        publisher = models.ForeingKey('Publisher')
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


Now on your project's urls.py, just add:

    urlpatterns = [
        ...
        path('api/', include(rest_api.urls)),
    ]

Under the hood, Boogie creates the Serializer and ViewSet classes for each
model using Django REST Framework  and configure a router that organizes every
end-point declared. Boogie enforces API versioning, so you should point your
browser to "/api/v1/" to see something like this:

    {
        "books": "https://my-site.com/api/v1/books/",
        "authors": "https://my-site.com/api/v1/authors/",
        "publishers": "https://my-site.com/api/v1/publishers/"
    }

Each resource is then constructed automatically according to the information
passed to the rest_api decorator. In our case, it exposes all fields of each
model and stores foreign relations as hyperlinks under a "links" property:

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


Versions
========