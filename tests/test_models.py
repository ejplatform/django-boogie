import pytest

from boogie.testing.pytest import ModelTester
from tests.testapp.models import Book, User


class TestBook(ModelTester):
    model = Book
    representation = 'title (author)'

    @pytest.fixture
    def book(self, author):
        return Book(title='title', author=author)

    @pytest.fixture
    def author(self):
        return User(name='author')
