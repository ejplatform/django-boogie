import pytest
from django.core.exceptions import ValidationError

from boogie.experimental.colors.models import Color


class TestColor:
    @pytest.fixture
    def color(self):
        return Color(name="red", hex_value="#FF0000")

    def test_color_representation(self, color):
        assert str(color) == "red: #FF0000"

    def test_color_with_invalid_value(self, db):
        color = Color(name="invalid", hex_value="*")
        with pytest.raises(ValidationError):
            color.full_clean()

    def test_color_with_valid_value(self, db):
        color = Color(name="invalid", hex_value="#FF0000")
        color.full_clean()
