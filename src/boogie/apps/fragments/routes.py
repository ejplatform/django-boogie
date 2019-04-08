from boogie.router import Router

from . import models

app_name = "fragments"
urlpatterns = Router(
    models={"fragment": models.Fragment}, lookup_field={"fragment": "ref"}
)


@urlpatterns.route("<model:fragment>")
def index(request, fragment):
    return fragment.render(request)
