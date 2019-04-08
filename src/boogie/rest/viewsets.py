from rest_framework import viewsets, status
from rest_framework.response import Response


class RestAPIBaseViewSet(viewsets.ModelViewSet):
    """
    Standard boogie view set.
    """

    queryset = None
    serializer_class = None
    lookup_field = None
    base_name = None
    api_version = None

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PermissionError as exc:
            return wrap_permission_error(exc)

    def perform_destroy(self, instance):
        self.delete_hook(self.request, instance)

    def delete_hook(self, request, instance):
        instance.delete()

    def get_queryset(self):
        return self.query_hook(self.request, self.queryset).all()

    def query_hook(self, request, qs):
        return qs


def wrap_permission_error(error):
    return Response({"error": "permission", "code": 403, "message": str(error)})
