from sidekick import import_later

from boogie.models import F

pd = import_later('pandas')


class TestQuerySetIndexing:
    def test_django_slicing_still_works(self, authors):
        assert authors[0] == authors.first()
        assert authors[-1] == authors.last()
        assert list(authors[0:2]) == [authors[0], authors[1]]

    def test_simple_2d_slicing(self, authors):
        author = authors.get(pk=1)
        assert authors[1, :] == author
        assert authors[1, 'name'] == author.name
        assert authors[1, ['name', 'age']] == [author.name, author.age]

    def test_2d_slicing_of_querysets(self, authors):
        assert_equal(authors[:, :], authors.all())
        assert_equal(authors[:, 'name'], authors.values_list('name', flat=True))
        assert_equal(authors[:, ['name', 'age']], authors.values_list('name', 'age'))

    def test_F_expression_slicing(self, authors):
        assert_equal(authors[F.age > 25, 'name'],
                     authors.filter(age__gt=25).values_list('name', flat=True))
        assert_equal(authors[F.age > 25, F.name],
                     authors.filter(age__gt=25).values_list('name', flat=True))
        assert_equal(authors[F.age > 25, [F.name, F.age]],
                     authors.filter(age__gt=25).values_list('name', 'age'))


class TestPandasIntegration:
    def test_queryset_to_dataframe(self, authors):
        df = authors[:, ['name', 'age']].dataframe()
        assert (df['name'] == ['Author', 'Young', 'Old']).all()
        assert df['age'].equals(pd.Series([float('nan'), 18, 80], index=df.index))


def assert_equal(qs1, qs2):
    assert list(qs1) == list(qs2)
