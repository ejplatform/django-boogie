import pytest
from django.db import IntegrityError
from hyperpython import FragmentNotFound

from boogie.apps.fragments import fragment, Format
from boogie.apps.fragments.models import Fragment

pytestmark = pytest.mark.django_db


class TestFragment:
    @pytest.fixture
    def fragment(self):
        return Fragment(
            ref='ref',
            title='title',
            format=Format.HTML_TRUSTED,
            content='content'
        )

    @pytest.fixture
    def fragment_db(self, fragment, db):
        fragment.save()
        return fragment

    def test_get_missing_fragment(self, db):
        with pytest.raises(FragmentNotFound):
            fragment('ref', raises=True)
        frag = fragment('ref')
        assert str(frag) == '<div class="error">Missing "ref" fragment</div>'

    def test_get_existing_fragment(self, fragment_db):
        data = fragment('ref')
        assert str(data) == 'content'

    def test_fragment_model(self, fragment):
        assert str(fragment) == 'ref'
        assert fragment.__html__() == 'content'

    def test_locked_fragment_cannot_be_deleted(self, fragment_db):
        fragment_db.lock()
        with pytest.raises(IntegrityError):
            fragment_db.delete()
