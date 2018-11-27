import pytest

from boogie.testing.factories import factory
from tests.testapp import factories
from tests.testapp.models import User


@pytest.fixture
def library(db):
    return factories.library()


@pytest.fixture
def authors(db):
    return factories.authors()


@pytest.fixture
def books(db):
    return factories.books()


@pytest.fixture
def user(db):
    return factory(User).create()


@pytest.fixture
def admin(db):
    user = factory(User).create()
    user.is_superuser = user.is_staff = True
    return user
