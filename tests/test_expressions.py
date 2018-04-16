from django.db import models

from boogie.models import F


class TestReadOnlyQueries:
    def assert_qs_equal(self, qs1, qs2):
        assert list(qs1) == list(qs2)

    def test_select_by_field_value(self, authors):
        qs = authors.filter(F.name == 'Old')
        assert len(qs) == 1

        author, = qs
        assert author.name == 'Old'
        assert author.age == 80

    def test_select_different(self, authors):
        qs = authors.filter(F.name != 'Old')
        assert len(qs) == 2

    def test_select_by_comparison(self, authors):
        assert authors.filter(F.age < 18).count() == 0
        assert authors.filter(F.age <= 18).count() == 1
        assert authors.filter(F.age > 18).count() == 1
        assert authors.filter(F.age >= 18).count() == 2

    def test_subfield_access(self, books):
        assert (F.author.name)._name == F('author__name').name

        self.assert_qs_equal(
            books.values_list('author__name'),
            books.values_list(models.F('author__name'))
        )
        self.assert_qs_equal(
            books.values_list('author__name'),
            books.values_list(F('author__name'))
        )
        self.assert_qs_equal(
            books.values_list('author__name'),
            books.values_list(F.author.name)
        )

    def test_string_operations(self, authors):
        assert list(authors.values_list(F.name.upper(), flat=True)) == \
               ['AUTHOR', 'YOUNG', 'OLD']

        assert list(authors.values_list(F.name.lower(), flat=True)) == \
               ['author', 'young', 'old']

        assert list(authors.values_list(F.name.length(), flat=True)) == \
               [6, 5, 3]

    def test_string_filtering(self, authors):
        qs = authors.filter(F.name.equals('old', case=False))
        assert qs[0].name == 'Old'

        qs = authors.filter(F.name.regex('^\w\w\w$'))
        assert qs[0].name == 'Old'

        qs = authors.filter(F.name.startswith('Ol'))
        assert qs[0].name == 'Old'

        qs = authors.filter(F.name.endswith('ld'))
        assert qs[0].name == 'Old'

        qs = authors.filter(F.name.has_substring('ld'))
        assert qs[0].name == 'Old'

    def test_statistical_functions(self, authors):
        res = authors.aggregate(
            F.age.min(),
            F.age.mean(),
            F.age.max(),
            # F.age.std(),
            # F.age.var(),
            F.age.count(),
        )
        assert res == dict(
            age__min=18,
            age__max=80,
            age__mean=(18 + 80) / 2,
            age__count=2,
        )


def _test_authors_ordering(self, authors):
    assert list(authors.values_list(-F.name, flat=True)) == ['Young', 'Old',
                                                             'Author']
