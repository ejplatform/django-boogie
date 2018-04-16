import pytest

from boogie.fields.enum_type import IntEnum, TaggedInt
from tests.testapp.models import User, Gender


class TestBasicEnum:
    @pytest.fixture
    def Gender(self):
        class Gender(IntEnum):
            MALE = 'male'
            FEMALE = 'female'
            OTHER = 'other'
            NOT_GIVEN = 'not given'

        return Gender

    def test_creates_proper_enum(self, Gender):
        assert [Gender.MALE, Gender.FEMALE, Gender.OTHER, Gender.NOT_GIVEN] == \
               [0, 1, 2, 3]

    def test_provides_item_descriptions(self, Gender):
        assert Gender.MALE_DESCRIPTION == 'male'
        assert Gender.MALE.get_description() == 'male'
        assert Gender.get_description(Gender.MALE) == 'male'
        assert Gender.get_description('MALE') == 'male'


class TestExplicitlyOrderedEnum(TestBasicEnum):
    @pytest.fixture
    def Gender(self):
        class Gender(IntEnum):
            OTHER = 2, 'other'
            FEMALE = 1, 'female'
            NOT_GIVEN = 3, 'not given'
            MALE = 0, 'male'

        return Gender


class TestTaggedIntEnum(TestBasicEnum):
    @pytest.fixture
    def Gender(self):
        class Gender(IntEnum):
            OTHER = TaggedInt(2, 'other')
            FEMALE = TaggedInt(1, 'female')
            NOT_GIVEN = TaggedInt(3, 'not given')
            MALE = TaggedInt(0, 'male')

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
