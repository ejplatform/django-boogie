import pytest

from boogie.models.utils import LazyMethod
from boogie.utils.text import humanize_name, plural, indent, safe_repr, snake_case, dash_case, first_line


class TestLazyMethod:
    @pytest.fixture(scope='session')
    def cls(self):
        method = LazyMethod('collections:MutableMapping.update')
        return type('Class', (dict,), {'update': method})

    def test_can_load_method_lazily(self, cls):
        d = cls()
        d.update(answer=42)
        assert d == {'answer': 42}


class TestTextFunctions:
    def test_text_functions(self):
        assert humanize_name('SomeName') == 'Some Name'
        assert humanize_name('some_name') == 'some name'
        assert dash_case('foo_bar') == 'foo-bar'
        assert snake_case('foo-bar') == 'foo_bar'
        assert dash_case('fooBar') == 'foo-bar'
        assert snake_case('fooBar') == 'foo_bar'
        assert plural('foo bar') == 'foo bars'
        assert indent('foo\nbar') == '    foo\n    bar'
        assert first_line('foo\nbar') == 'foo'

    def test_safe_repr(self):
        assert safe_repr('foo') == repr('foo')

        class BadRepr:
            def __repr__(self):
                raise ValueError

        assert safe_repr(BadRepr()) == '<BadRepr object [ValueError: ]>'
