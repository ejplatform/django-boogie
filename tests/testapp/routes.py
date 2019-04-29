from django.http import JsonResponse, HttpResponse
from hyperpython import div, a

from boogie import router
from . import models

urlpatterns = router.Router(
    template='testapp/{name}.jinja2',
    models={
        'user': models.User,
        'book': models.Book,
    },
    lookup_field={
        'user': 'id',
    },
)


@urlpatterns.route('hello/')
def hello_world(request):
    return '<Hello World>'


@urlpatterns.route('hello-simple/')
def hello_world_simple():
    return 'Hello World!'


@urlpatterns.route('hello/<name>/')
def hello_name(name):
    return f'Hello {name}!'


@urlpatterns.route('hello/<name>.json')
def hello_json(name):
    return JsonResponse({'message': 'hello', 'name': name})


@urlpatterns.route('hello/response/<name>/')
def hello_response(name):
    return HttpResponse(b'Hello %b' % name.encode('utf8'))


@urlpatterns.route('book/<model:book>/')
def book(book):
    return str(book)


@urlpatterns.route('links/')
def links():
    return div([
        a('hello', href='/hello/'),
        a('hello-simple', href='/hello-simple/'),
        a('hello me', href='/hello/me/'),
    ])
