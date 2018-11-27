=======
Testing
=======

We all know that all software should be extensively tested, but who has time
for it? ;)


Testing views (pytest only)
===========================

Ideally your views should be minimalistic and require very little testing.
Boogie automates simple tests that simply request a view without any complex
validation of the response.

Depending on the complexity of your frontend and/or how the view functions are
organized, those automated tests barely scratch the surface. Either way, the
test classes in this module are a good starting point for more comprehensive
tests for the views of your application.

.. module:: boogie.testing.pytest

Web Crawler
-----------

Perhaps the most convenient test class in this module is the :class:`CrawlerTester`.
You just override a few parameters in the sub-class and it will start crawling
pages in your web site looking for broken links and invalid responses.

.. code-block:: python

    # test_urls.py
    import pytest
    from boogie.testing.pytest import CrawlerTester


    class TestPublicUrls(CrawlerTester):
        ... # TODO


    # Now we repeat the same tests, but with a different user fixture.
    class TestUserUrls(TestPublicUrls):
        must_visit = ('/profile/', '/logout/')

        @pytest.fixture
        def user(self, db):
            return factories.make_user()


Explicit
--------

Sometimes it is necessary to offer a more fine-grained control of the URLs that
should be visited. Web crawling based tests can be very slow and are hard to
isolate. They are a nice when doing "integration tests", but are really poor
to cover specific apps or functions.

:class:`UrlTester` provides a more fine grained option for testing the URLs of an
specific app.

.. code-block:: python

    # test_urls.py
    from boogie.testing.pytest import UrlTester


    class TestUrls(UrlTester):
        ... # TODO




API Reference
-------------


.. autoclass:: URLTester
    :members:

.. autoclass:: CrawlerTester
    :members:



Testing models
==============

# TODO


Fixtures
========

.. module:: boogie.testing.factories


Boogie integrates both `Factory Boy`_ and `Model Mommy`_ projects. While there
is a lot of overlap between both projects, there are some unique features of
each project that complement the other.

.. _Factory Boy: https://factoryboy.readthedocs.io/en/latest/
.. _Model Mommy: https://model-mommy.readthedocs.io/en/latest/

Currently, the only public API is the factory() function:

.. ignore-next-block
.. code-block:: python

    # on factories.py
    # Notice we do not have to specify default values even for required fields.
    # ModelMommy fills those entries with random data.
    user = factory(User)
    admin = factory(User, is_superuser=True, is_staff=True)

    # on tests.py
    from .factories import *

    # We use factory.create(**optional_kwargs) to create new instances.
    # Use .build() instead of .create() to preventing saving on the db.
    def test_user_can_edit_blog(user, admin, db):
        assert not user.create().can_edit_blog()
        assert not admin.create().can_edit_blog()



API Reference
-------------

.. autofunction:: factory


Mocks
=====

.. module:: boogie.testing.mock

Mocks are very useful in tests. A prevalent use of mocks can greatly reduce
unnecessary trips to the database which can be very costly and usually is the
major factor in making test suites of web-based apps slow.

You may want to optimize even further by recognizing that unittest.mock Mocks are
really slow compared to more lightweight Python objects. Boogie provides very
lightweight Mock classes and context managers that helps saving a few CPU cycles.


API Reference
-------------

.. autoclass:: LightMock
.. autofunction:: mock_save
.. autofunction:: assume_unique
.. autofunction:: raise_exception


Boogie Client
=============

.. module:: boogie.testing.client

Boogie implements a Django Client subclass that adds a few extra methods that
can be useful in testing and on interactive environments such as Jupyter
notebooks.

The boogie client can be accessed as a fixture from the boogie.testing.pytest
module. There are a few different flavors:

client:
    Standard client for a anonymous user.
user_client:
    Client logged in as "user".
admin_client:
    Client logged in as "admin/superuser".
author_client:
    Client logged in as "author". Author is the owner of some resource.


API Reference
-------------

.. autoclass:: Client
    :members:


Debug
=====

.. module:: boogie.debug

Boogie special module ``boogie.debug`` implements a few functions that helps
with debugging code. This module uses lots of dirty hacks and non-standard
practices and should never be enabled in a production environments. It is, however,
very convenient to track bugs and other forms of exploration.


API Reference
-------------

.. autofunction:: info
.. autofunction:: embed
.. autofunction:: set_trace
.. autofunction:: enable_debugging
