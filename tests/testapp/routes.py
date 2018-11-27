from hyperpython import div, a

from boogie import router

urlpatterns = router.Router(
    template='testapp/{name}.jinja2',
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


@urlpatterns.route('links/')
def links():
    return div([
        a('hello', href='/hello/'),
        a('hello-simple', href='/hello-simple/'),
        a('hello me', href='/hello/me/'),
    ])
