from boogie import db
from tests.testapp.models import User


class TestDbObject:
    def test_simple_api(self):
        assert db.testapp.user_model is User
        assert db.testapp.users is User.objects
        assert db.testapp.user_objects is User.objects
