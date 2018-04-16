from boogie import db
from tests.testapp.models import User


class TestDbObject:
    def test_simple_api(self):
        assert db.testapp.user is User.objects
