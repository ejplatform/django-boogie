from collections import defaultdict

import pytest
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
        print(router.lookup_field)
        print(route.lookup_field)
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
            'Error fetching /invalid/, invalid get_response: 404\n'
            'Error fetching /bad/, invalid get_response: 404\n'
        )
        assert str(exc.value) == "errors found: ['/bad/', '/invalid/']"


class TestUrlCrawl(CrawlerTester):
    start = ['/links/']
    user = 'user'
    must_visit = ['/hello/me/']
