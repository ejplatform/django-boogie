from collections import defaultdict

from boogie.router import Router


class TestRouter:
    def test_router_pass_parameters_to_route(self):
        router = Router(lookup_type='slug', lookup_field='title')
        assert isinstance(router.lookup_field, defaultdict)
        assert isinstance(router.lookup_type, defaultdict)

        # Register route without override
        route = router.register(lambda book: None)
        assert isinstance(route.lookup_field, defaultdict)
        assert isinstance(route.lookup_type, defaultdict)
        print(router.lookup_field)
        print(route.lookup_field)
        assert route.lookup_field['book'] == 'title'
        assert route.lookup_type['book'] == 'slug'

        # Override field
        route = router.register(lambda book: None, lookup_field='author')
        assert route.lookup_field['book'] == 'author'
        assert route.lookup_type['book'] == 'slug'

        # Override type
        route = router.register(lambda book: None, lookup_type='str')
        assert route.lookup_field['book'] == 'title'
        assert route.lookup_type['book'] == 'str'

        # Override type with dict
        route = router.register(lambda book: None, lookup_type={'book': 'str'})
        assert route.lookup_field['book'] == 'title'
        assert route.lookup_type['book'] == 'str'
