import pytest

from boogie.utils import linear_namespace
from boogie.utils.linear_namespace import linear_namespace_cached


class TestLinearNamespace:
    @pytest.fixture(scope='class')
    def point(self):
        return linear_namespace('Point', ['x', 'y'])

    def test_linear_namespace_behaves_as_a_namedlist(self, point):
        pt = point(1, 2)
        assert pt.x == pt[0] == 1
        assert pt.y == pt[1] == 2
        assert tuple(pt) == (1, 2)
        assert len(pt) == 2
        assert list(pt) == [1, 2]
        assert pt == [1, 2]
        assert pt == point(1, 2)
        assert pt == point(x=1, y=2)
        assert pt != point(2, 1)
        assert repr(pt) == 'Point(1, 2)'

    def test_list_composition_functions(self, point):
        pt = point(1, 2)
        assert type(pt + [1, 2]) is list

        assert pt + pt == [1, 2, 1, 2]
        assert pt + [1, 2] == [1, 2, 1, 2]
        assert pt * 2 == [1, 2, 1, 2]

        assert [1, 2] + pt == [1, 2, 1, 2]
        assert 2 * pt == [1, 2, 1, 2]

    def test_comparison(self, point):
        pt = point(1, 2)
        assert pt != [1, 1]
        assert pt > [1, 1]
        assert pt >= pt
        assert pt <= pt
        assert pt < [1, 3]

    def test_linear_namespace_mutation(self, point):
        pt = point(1, 2)
        assert pt == [1, 2]

        pt.y = 1
        assert pt == [1, 1]

        pt[0] = 0
        assert pt == [0, 1]

    def test_assert_cannot_change_size_with_full_slice_mutation(self, point):
        pt = point(1, 2)
        pt[:] = 3, 4
        assert pt == [3, 4]

        with pytest.raises(ValueError):
            pt[:] = 3, 4, 5

    def test_list_api(self, point):
        pt = point(1, 2)
        assert pt.index(1) == 0
        assert pt.count(2) == 1

        pt.reverse()
        assert pt == [2, 1]

        pt.sort()
        assert pt == [1, 2]

    def test_linear_namespace_from_sequence(self, point):
        fromseq = linear_namespace.fromseq(point, [1, 2])
        assert fromseq == point.fromseq([1, 2]) == point(1, 2)

    def test_linear_namespace_from_wrong_sequence(self, point):
        with pytest.raises(ValueError):
            point.fromseq([1, 2, 3])

    def test_invalid_field_names(self):
        for fields in [['01'], ['x', '01'], ['_fields'], ['x', 'x']]:
            with pytest.raises(ValueError):
                linear_namespace('Test', fields)

    def test_cached_type_does_not_return_a_copy(self, point):
        point1 = linear_namespace_cached('Point', ['x', 'y'])
        point2 = linear_namespace_cached('Point', ['x', 'y'])
        assert point is not point1
        assert point1 is point2
