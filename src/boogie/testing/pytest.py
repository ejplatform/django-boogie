import copy
from itertools import chain

import pytest
from _pytest.fixtures import FixtureLookupError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.http import Http404
from django.urls import resolve

from .client import Client
from .crawler import check_link_errors
from .urlchecker import LOGIN_REGEX, UrlChecker as _UrlChecker
from ..utils.text import snake_case

User = get_user_model()


#
# Fixture classes
#
class UserFixtures:
    """
    Create the anonymous, user, author and admin fixtures:

    anonymous:
        An anonymous user.
    user:
        Represents regular user with no special privileges on the platform.
    author:
        Another regular user, but we assume it to be the owner of some
        specific resource. A test scenario may create an ``user``, an ``author``
        and some page with ``page.owner = author``
    admin:
        A user with superuser permissions.

    For each user, it creates a corresponding client_<user> fixture that
    initializes a client logged in with the given user.
    """

    @pytest.fixture
    def anonymous(self, db):
        return AnonymousUser()

    @pytest.fixture
    def user(self, db):
        return self.make_user("user", email="user@user.com")

    @pytest.fixture
    def author(self, db):
        return self.make_user("author", email="author@author.com")

    @pytest.fixture
    def admin(self, db):
        return self.make_user(
            "admin", email="admin@admin.com", is_superuser=True, is_staff=True
        )

    @pytest.fixture
    def client(self, db):
        """Standard test client"""
        return Client()

    @pytest.fixture
    def user_client(self, db, client, user):
        """Client logged in as 'user'"""
        return self._with_login(client, user)

    @pytest.fixture
    def author_client(self, db, client, author):
        """Client logged in as 'author'"""
        return self._with_login(client, author)

    @pytest.fixture
    def admin_client(self, db, client, admin):
        """Client logged in as 'admin'"""
        assert admin.is_staff, f"User {admin} does not have staff privileges"
        assert admin.is_superuser, f"User {admin} does not have superuser privileges"
        return self._with_login(client, admin)

    def _with_login(self, client, user):
        # We create a copy because we don't want to share state between the
        # different client fixtures.
        client = copy.copy(client)
        client.force_login(user)
        return client

    def make_user(self, name, email, is_superuser=False, is_staff=False, **kwargs):
        """
        Creates a new user.

        Subclasses may override this function and it must accept the following
        arguments.

        Args:
            name:
                Fixture name for the user.
            email:
                User's e-mail.
            is_staff, is_superuser (bool):
                Tells if user can access the admin interface (staff) or is a
                sysadmin (superuser).
        """
        model = get_user_model()
        kwargs.update(is_superuser=is_superuser, is_staff=is_staff, email=email)
        return model.objects.create_user(name, **kwargs)


#
# URL Tester
#
class UrlTester(UserFixtures):
    """
    Test if users can access all paths in the "paths" attribute with a
    successful HTTP status code.

    Most of the logic for this class is implemented by
    :class:`boogie.testing.urlchecker.URLChecker` class.

    Examples:

        A UrlTester subclass must define the following (optional) attributes:

        .. code-block:: python

            class TestSomeAppUrls(UrlTester):
                # "paths" is a dictionary describing which paths can be
                # accessed by each user. Remember always using absolute paths.
                paths = {
                    # Use None to specify URLs that can be accessed by
                    # anonymous users.
                    None: [
                        '/some-app/',
                        '/some-app/url-a/',
                        '/some-app/url-b.json',
                    ],

                    # Other users are specified by strings which, during
                    # testing, are interpreted as fixture names.
                    'user': [
                        '/some-app/private/',
                        '/some-app/private-2/',
                    ],

                    # The list of paths is cumulative, i.e., "admin" inherits
                    # all URLs from "user", which inherits all URLs from None.
                    'admin': [
                        '/some-app/admin-panel/,
                        '/some-app/super-secret/,
                    ],
                }

                # The post_paths attr behaves similarly to paths, but specify
                # some payload data which is sent with a POST request.
                post_paths = {
                    None: {
                        '/some-app/form/: {
                            'name': 'Someone',
                            'email': 'some@email.com',
                        },
                    },

                    # Like paths, it re-uses entries associated with the
                    # previous fixtures. However, if a URL is repeated,
                    # it overrides the POST data.
                    'user': {
                        '/some-app/form/: {
                            'name': 'user',
                            'email': 'user@user.com',
                        },
                    },

                    # Append some unique #anchor to the path string to re-use
                    # the path of a previous user and include a new test data.
                    'admin': {
                        '/some-app/form/#admin: {
                            'name': 'admin',
                            'email': 'user@user.com',
                        },
                    },
                }

                # The URL tester will load a class scoped "data" fixture, if
                # available. This can be used to populate the database with
                # additional models necessary for the test to complete.
                @pytest.fixture
                def data(self, db):
                    models.Model1.objects.create(...)
                    models.Model2.objects.create(...)


                # Each user corresponds to a fixture in the database. We
                # automatically try to create a "user", "author" and "admin"
                # users. Of course you may want/need to personalize the creation
                # of those fixtures if you want.
                @pytest.fixture
                def user(self, db):
                    # The default user is created with the following command.
                    # The other fixtures follow a similar pattern.
                    return self.make_user('user', email='user@user.com')
    """

    paths: dict = {}
    post_paths: dict = {}
    login_regex: str = LOGIN_REGEX
    url_checker = _UrlChecker

    @pytest.fixture
    def data(self):
        return None

    @pytest.fixture
    def client(self, db):
        return Client()

    @pytest.mark.django_db
    def test_urls(self, request, client, data):
        """
        Implements the logic used by the dynamic test_urls class.
        """
        users = self.get_user_fixtures(request)
        kwargs = {"login_regex": self.login_regex, "client": client}
        checker = self.url_checker(self.paths, self.post_paths, **kwargs)
        errors = checker.check_url_errors(users=users)
        if errors:
            for url, value in errors.items():
                code = value.status_code
                print(f"Error fetching {url}, invalid response: {code}")
            raise AssertionError(f"errors found: {sorted(errors)}")

    def get_user_fixtures(self, request):
        """
        Creates a dictionary mapping names of user fixtures to their respective
        values.
        """
        users = set(chain(self.paths, self.post_paths))
        users.discard(None)
        return {user: request.getfixturevalue(user) for user in users}


#
# Web crawling
#
class CrawlerTester:
    """
    Base class for tests based on crawling your website from a initial URL.

    Can be configured by overriding the following attributes:

        start (path or list of paths):
            A url or a list of urls used as the starting points for the crawler.
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

    start = "/"
    user = "user"
    skip_patterns = ()
    skip_urls = ()
    xfail = ()
    must_visit = ()
    log = print
    error_class = AssertionError

    @pytest.fixture
    def conf(self, request):
        return {"user": request.getfixturevalue("user")}

    @pytest.mark.django_db
    def test_reaches_all_urls(self, request, conf):
        """
        Test if it fails in some view when crawling from a starting URL.
        """
        try:
            request.getfixturevalue("data")
        except FixtureLookupError:
            pass

        errors = {}
        user = conf["user"]
        start = self.start
        if isinstance(start, str):
            start = [start]

        for url in start:
            try:
                check_link_errors(
                    url,
                    visit=self.must_visit,
                    errors=self.xfail,
                    user=user,
                    skip_patterns=self.skip_patterns,
                    skip_urls=self.skip_urls,
                    log=self.log,
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
    Perform some standard test on a given model

    This class assumes the presence of an "instance" fixture that creates an
    exemplary of the model class.

    Attributes:
        model (model class):
            The model class that to be tested.
        representation (str):
            Expected value of str(instance)
        absolute_url:
            Expected value of instance.get_absolute_url()
    """

    model: type
    representation: str
    absolute_url: str
    db = False

    @pytest.fixture
    def instance(self, request):
        model_name = snake_case(self.model.__name__)
        name = getattr(self, "instance_fixture", model_name)
        if self.db:
            request.getfixturevalue("db")
        try:
            return request.getfixturevalue(name)
        except FixtureLookupError:
            return self.get_instance()

    def get_instance(self):
        """
        Fallback method that is executed when the instance or model fixtures are
        not defined.
        """
        model_name = snake_case(self.model.__name__)
        raise ImproperlyConfigured(
            f'please either define an "instance" or "{model_name}"\n'
            f'fixture in your class or implement the "get_instance" method'
        )

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
        got = str(instance)
        expect = self.representation
        if expect != got:
            msg = "invalid representation: expect: %r, got: %r"
            raise AssertionError(msg % (expect, got))

            # Check absolute url
        if hasattr(model, "get_absolute_url"):
            assert instance.get_absolute_url() == self.absolute_url
            try:
                resolve(self.absolute_url)
            except Http404:
                raise AssertionError("absolute_url resulted on a 404")

        # Run examples
        for name, example in self.get_examples().items():
            if name == "clean":
                example.full_clean()
            elif example == "invalid":
                with pytest.raises(ValidationError):
                    example.full_clean()
            else:
                raise ImproperlyConfigured(f"invalid example: {name}")

    def check_improperly_configured(self, instance):
        """
        Check if test class was correctly set up for instance.
        """
        model = self.model
        requires_url = hasattr(model, "get_absolute_url")

        # Check success
        if hasattr(self, "representation") and (
            hasattr(self, "absolute_url") or not requires_url
        ):
            return

        print(
            "HINT: You can create a valid tester class by replacing it by\n"
            "the following code:"
        )
        print(make_test_class(self, instance))
        print("\nPlease revise to see if inferred properties are correct.")
        raise ImproperlyConfigured("Model tester class is not configured")


#
# Utility
#


def make_test_class(model_tester, instance):
    """
    Return a string with a plausible source code representation for a
    ModelTester test class.
    """

    base_names = ", ".join(cls.__name__ for cls in type(model_tester).__bases__)
    base = f"""
    class {model_tester.__class__.__name__}({base_names}):
        model = models.{instance.__class__.__name__}
        representation = {repr(str(instance))}"""
    if model_tester.db:
        base += "\n        db = True"
    if hasattr(instance, "get_absolute_url"):
        base += "\n        absolute_url = {instance.get_absolute_url()!r}"
    return base
