from rest_framework.response import Response

from boogie.rest import rest_api
from rest_framework.viewsets import ViewSet


@rest_api.register_viewset('numbers')
class NumbersViewSet(ViewSet):
    base_name = 'number'

    def list(self, request):
        return Response([{'idx': i, 'value': i ** 2} for i in range(1, 11)])

    def retrieve(self, request, pk=None):
        i = int(pk)
        return Response({'idx': i, 'value': i ** 2})


@rest_api.property('testapp.User')
def first_name(user):
    return user.name.partition(' ')[0]
