from django.db.models import Model
from sidekick import Record, field


class Route(Record):
    """
    Define a route in routes.py

    This is analogous to the url() function in Django.
    """
    route = field(str)
    model = field(Model)
    serializer = field(default=None)
    fields = field(default=None)
    viewset = field(default=None)


def include_router(name):
    """
    Include routes from a routes in your urls.py module.

    This function is used to include routes from a urls.py module and works
    analogously to Django's builtin include() function.
    """
