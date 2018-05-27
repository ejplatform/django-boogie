import pytest

from boogie.fields.enum_type import IntEnum, Enum
from tests.testapp.models import User, Gender


class TestBasicEnum:
    @pytest.fixture
    def gender(self):
        class Gender(IntEnum):
            MALE = 'male'
            FEMALE = 'female'
            OTHER = 'other'
            NOT_GIVEN = 'not given'

        return Gender

    def test_creates_proper_enum(self, gender):
        assert [gender.MALE, gender.FEMALE, gender.OTHER, gender.NOT_GIVEN] == \
               [0, 1, 2, 3]

    def test_provides_item_descriptions(self, gender):
        assert gender.MALE_DESCRIPTION == 'male'
        assert gender.MALE.description == 'male'
        assert gender.get_description(gender.MALE) == 'male'
        assert gender.get_description('MALE') == 'male'


class TestExplicitlyOrderedEnum(TestBasicEnum):
    @pytest.fixture
    def gender(self):
        class Gender(IntEnum):
            OTHER = 2, 'other'
            FEMALE = 1, 'female'
            NOT_GIVEN = 3, 'not given'
            MALE = 0, 'male'

        return Gender


class TestEnumField:
    @pytest.fixture
    def user(self):
        return User(name='user', gender=Gender.FEMALE)

    def test_enum_field_contribute_to_class(self, user):
        assert user.gender == user.GENDER_FEMALE
        assert user.GENDER_MALE == Gender.MALE

    def test_enum_field_survive_round_trip(self, db, user):
        user.save()
        new = User.objects.get(id=user.id)
        assert new.gender is not None
        assert isinstance(new.gender, Gender)
        assert new.gender == Gender.FEMALE

    def test_enum_field_handle_string_inputs(self, db, user):
        user.gender = 'FEMALE'
        user.save()
        new = User.objects.get(id=user.id)
        assert new.gender is not None
        assert isinstance(new.gender, Gender)
        assert new.gender == Gender.FEMALE


class TestNonIntEnumField:
    def test_make_non_numeric_enum_field(self):
        class Gender(Enum):
            MALE = 'male', 'male'
            FEMALE = 'female', 'female'
            OTHER = 'other', 'other'
            NOT_GIVEN = 'not-given', 'not given'

        assert Gender.MALE == 'male'
        assert Gender.MALE_DESCRIPTION == 'male'
        assert Gender.NOT_GIVEN == 'not-given'
        assert Gender.NOT_GIVEN_DESCRIPTION == 'not given'
        assert Gender.NOT_GIVEN.description == 'not given'
        assert Gender.get_description('NOT_GIVEN') == 'not given'
        assert Gender.get_description(Gender.NOT_GIVEN) == 'not given'
