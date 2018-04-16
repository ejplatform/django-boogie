Django Rest Framework (WIP)
===========================

Django Rest Framework (DRF) is very powerful and flexible, but unfortunately
requires a lot of boilerplate. This is aggravated if we want to build a level
3 REST API (link) with HATEAOS controls. This is how REST is supposed to work
and we should really aim for this kind organization. Boogie makes it easy to
create simple RESTful APIs.


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

This will create the following endpoints under "/api/v1/"


    {
        "books": "https://my-site.com/api/v1/books/",
        "authors": "https://my-site.com/api/v1/authors/",
        "publishers": "https://my-site.com/api/v1/publishers/"
    }

If you go to one of those endpoints, you will get something like this:

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