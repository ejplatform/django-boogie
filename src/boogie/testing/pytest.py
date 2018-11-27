from functools import lru_cache

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.http import Http404
from django.urls import resolve

from .client import Client
from .crawler import check_link_errors
from .urlchecker import LOGIN_REGEX, UrlChecker as _UrlChecker
from ..utils.text import snake_case

User = get_user_model()


#
# URL Tester
#
class URLTesterMeta(type):
    """
    Metaclass for UrlTester.
    """

    def __new__(mcs, name, bases, namespace, base=False):
        not_none = (lambda x: x is not None)
        users = tuple(sorted({
            *filter(not_none, namespace.get('urls', {}).keys()),
            *filter(not_none, namespace.get('posts', {}).keys()),
        }))
        if not base:
            namespace['test_urls'] = make_test_urls(users)
        return type.__new__(mcs, name, bases, namespace)


class UrlTester(metaclass=URLTesterMeta, base=True):
    """
    Base class for tests.
    """

    @pytest.fixture
    def data(self):
        return None

    @pytest.fixture
    def user(self, db):
        return self.make_user('user', email='user@user.com')

    @pytest.fixture
    def author(self, db):
        return self.make_user('author', email='author@author.com')

    @pytest.fixture
    def admin(self, db):
        return self.make_user('admin', email='admin@admin.com',
                              is_superuser=True, is_staff=True)

    def make_user(self, *args, **kwargs):
        return User.objects.create_user(*args, **kwargs)

    urls = {}
    posts = {}
    login_regex = LOGIN_REGEX


#
# Web crawling
#
class CrawlerTester:
    """
    Base class for tests based on crawling your website from a initial URL.

    Can be configured by overriding the following attributes:

        bases (list of urls):
            List of (url, user) pairs used as the starting points of web
            crawling.
        skip (list of urls):
            URLs that should be skipped during testing. The crawler will never
            visit those URLs unless they are a starting url in bases.
        xfail (list of urls):
            URLs that are expected to have failures.
        must_visit (list of urls):
            Checks if all URLs in that list were visited after crawling ends.
        user (str):
            Name of user instance fixture.
    """

    root = '/'
    user = 'user'
    skip = ()
    xfail = ()
    must_visit = ()
    log = print
    error_class = AssertionError

    @pytest.fixture
    def data(self):
        return {None: None}

    @pytest.fixture
    def conf(self, request):
        return {'user': request.getfixturevalue('user')}

    @pytest.mark.django_db
    def test_reaches_all_urls(self, data, conf):
        """
        Test if it fails in some view when crawling from a starting URL.
        """
        errors = {}
        user = conf['user']
        root = self.root
        if isinstance(root, str):
            root = [root]

        for url in root:
            try:
                check_link_errors(
                    url, visit=self.must_visit, skip=self.skip,
                    errors=self.xfail, user=user, log=self.log,
                )
            except AssertionError as ex:
                errors.update(ex.args[0])
        if errors:
            raise self.error_class(errors)


#
# Testing models
#
class ModelTester:
    """
    A helper class that makes it easier for testing models.
    """
    model: type
    representation: str
    fixture_name: str
    absolute_url: str
    db = False

    @pytest.fixture
    def instance(self, request):
        if not hasattr(self, 'fixture_name'):
            name = snake_case(self.model.__name__)
        else:
            name = self.fixture_name
        if self.db:
            request.getfixturevalue('db')
        return request.getfixturevalue(name)

    def get_examples(self):
        """
        Return a dictionary with some exemplary models with expected
        characteristics. Sub-classes can define any one of the entries bellow::

        - clean: passes a .full_clean() check
        - invalid: raises ValidationError during .full_clean()
        """
        return {}

    def test_django_model_interface(self, instance):
        """
        Test if model implements a basic Django Model interface correctly.
        """
        model = self.model
        self.check_improperly_configured(instance)

        # Check representation
        assert str(instance) == self.representation

        # Check absolute url
        if hasattr(model, 'get_absolute_url'):
            assert instance.get_absolute_url() == self.absolute_url
            try:
                resolve(self.absolute_url)
            except Http404:
                raise AssertionError('absolute_url resulted on a 404')

        # Run examples
        for name, example in self.get_examples().items():
            if name == 'clean':
                example.full_clean()
            elif example == 'invalid':
                with pytest.raises(ValidationError):
                    example.full_clean()
            else:
                raise ImproperlyConfigured(f'invalid example: {name}')

    def check_improperly_configured(self, instance):
        """
        Check if test class was correctly set up for instance.
        """
        model = self.model
        requires_url = hasattr(model, 'get_absolute_url')

        # Check success
        if (hasattr(self, 'representation')
                and (hasattr(self, 'absolute_url') or not requires_url)):
            return

        print('HINT: You can create a valid tester class by replacing it by\n'
              'the following code:')
        print(make_test_class(self, instance))
        print('\nPlease revise to see if inferred properties are correct.')
        raise ImproperlyConfigured('Model tester class is not configured')


#
# Fixtures
#
@pytest.fixture
def client(db):
    """Standard test client"""
    return Client()


@pytest.fixture
def user_client(db, user):
    """Client logged in as 'user'"""
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def admin_client(db, admin):
    """Client logged in as 'admin'"""
    client = Client()
    client.force_login(admin)
    assert admin.is_staff, f'User {admin} does not have staff privileges'
    return client


@pytest.fixture
def author_client(db, author):
    """Client logged in as 'author'"""
    client = Client()
    client.force_login(author)
    return client


#
# Utilities
#
def make_test_class(model_tester, instance):
    """
    Return a string with a plausible source code representation for a
    ModelTester test class.
    """

    base_names = ', '.join(cls.__name__ for cls in type(model_tester).__bases__)
    base = f"""
    class {model_tester.__class__.__name__}({base_names}):
        model = models.{instance.__class__.__name__}
        representation = {repr(str(instance))}"""
    if model_tester.db:
        base += '\n        db = True'
    if hasattr(instance, 'get_absolute_url'):
        base += '\n        absolute_url = {instance.get_absolute_url()!r}'
    return base


@lru_cache(32)
def make_test_urls(users):
    """
    Create the test_urls() function for the given list of users.

    Users are passed to function as fixtures.
    """
    inputs = ', '.join(['data', 'db', 'client', *users])
    src = (
        f'def test_urls(self, {inputs}):\n'
        f'    check_urls_from_locals(locals())'
    )

    # Eval code and fetch result
    ns = {}
    exec(src, {'check_urls_from_locals': check_urls_from_locals}, ns)
    return ns['test_urls']


def check_urls_from_locals(variables):
    """
    Implements the logic used by the dynamic test_urls class.
    """
    self = variables.pop('self')
    variables.pop('data')
    variables.pop('db')
    client = variables.pop('client')
    checker = _UrlChecker(self.urls, self.posts,
                          self.login_regex, client=client)
    errors = checker.check_url_errors(users=variables)
    if errors:
        for url, value in errors.items():
            code = value.status_code
            print(f'Error fetching {url}: got status code {code}')
        raise AssertionError(f'errors found at given urls: {list(errors)}')
