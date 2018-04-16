import pytest

from tests.testapp import factories


@pytest.fixture
def library(db):
    return factories.library()


@pytest.fixture
def authors(db):
    return factories.authors()


@pytest.fixture
def books(db):
    return factories.books()
