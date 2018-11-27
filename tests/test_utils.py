import pytest
from boogie.models.utils import LazyMethod


class TestLazyMethod:
    @pytest.fixture(scope='session')
    def cls(self):
        method = LazyMethod('collections:MutableMapping.update')
        return type('Class', (dict,), {'update': method})

    def test_can_load_method_lazily(self, cls):
        d = cls()
        d.update(answer=42)
        assert d == {'answer': 42}
