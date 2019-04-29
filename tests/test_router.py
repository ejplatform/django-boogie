from collections import defaultdict

import pytest
from django.urls import reverse
from pytest import raises

from boogie.router import Router
from boogie.testing.pytest import UrlTester, CrawlerTester
from boogie.utils.text import redirect_output


class TestRouter:
    def test_router_pass_parameters_to_route(self):
        router = Router(lookup_type='slug', lookup_field='title')
        assert isinstance(router.lookup_field, defaultdict)
        assert isinstance(router.lookup_type, defaultdict)

        # Register route without override
        route = router.register(lambda book: None)
        assert isinstance(route.lookup_field, defaultdict)
        assert isinstance(route.lookup_type, defaultdict)
        assert route.lookup_field['book'] == 'title'
        assert route.lookup_type['book'] == 'slug'

        # Override field
        route = router.register(lambda book: None, lookup_field='author')
        assert route.lookup_field['book'] == 'author'
        assert route.lookup_type['book'] == 'slug'

        # Override type
        route = router.register(lambda book: None, lookup_type='str')
        assert route.lookup_field['book'] == 'title'
        assert route.lookup_type['book'] == 'str'

        # Override type with dict
        route = router.register(lambda book: None, lookup_type={'book': 'str'})
        assert route.lookup_field['book'] == 'title'
        assert route.lookup_type['book'] == 'str'


class TestAppUrlTester(UrlTester):
    paths = {
        None: [
            '/hello/',
            '/hello-simple/',
            '/hello/foo/',
        ],
        'user': [],
        'author': [],
        'admin': [],
    }

    def test_url_data(self, client):
        response = client.get('/hello/')
        assert response.content == b'&lt;Hello World&gt;'

        response = client.get('/hello/someone/')
        assert response.content == b'Hello someone!'

        response = client.get('/hello/someone.json')
        assert response.json() == {"message": "hello", "name": "someone"}
        assert response.content == b'{"message": "hello", "name": "someone"}'

        response = client.get('/hello/response/someone/')
        assert response.content == b'Hello someone'

    def test_routes_that_touch_db(self, client, book):
        # Get url that uses model
        response = client.get(f'/book/{book.id}/')
        assert response.content == b'Book (Author)'

        # 404 for non-existing models
        response = client.get(f'/book/42/')
        assert response.status_code == 404

        # Url reverse
        assert reverse('book', kwargs={'book': book}) == '/book/1/'
        assert reverse('book', kwargs={'book': '42'}) == '/book/42/'


class TestAppUrlTesterFailure(UrlTester):
    paths = {
        None: [
            '/invalid/',
            '/bad/',
        ],
        'user': [],
    }

    def make_user(self, name, email, **kwargs):
        if name == 'admin':
            raise ValueError(name, email)
        return super().make_user(name, email, **kwargs)

    def test_fails_to_make_admin(self, request):
        with raises(ValueError):
            request.getfixturevalue('admin')

    @pytest.mark.django_db
    def test_urls(self, request, client, data):
        with raises(AssertionError) as exc:
            with redirect_output() as out:
                super().test_urls(request, client, data)
        assert out.getvalue() == (
            'Error fetching /invalid/, invalid response: 404\n'
            'Error fetching /bad/, invalid response: 404\n'
        )
        assert str(exc.value) == "errors found: ['/bad/', '/invalid/']"


class TestUrlCrawl(CrawlerTester):
    start = ['/links/']
    user = 'user'
    must_visit = ['/hello/me/']
