=================
Class based views
=================

Old Django versions used generic function-based views. While those views were
convenient, the original implementation lacked composability: function-based
generic views implement common usage patterns, but were hard to modify and
reuse code across implementations. Now, Django introduced class-based views
to solve those problems. The new implementation, however, has its own set
of flaws: it is based on a very confusing inheritance tree [#link], and it
uses a confusing API that betrays the original simplicity of Django view
functions.

* It is not clear what is a View object: instances are never used directly
  and the API expect to be used via the View.as_view() class method.
* Data flow is unclear. In most generic views, the request, ``*args`` and ``**kwargs``
  are saved as attributes and are often also passed as argument of many
  internal methods. You can never anticipate when to use what, which is somewhat
  ameliorated by Django's excellent documentation ;)
* They are very stateful objects. Some people may find it distasteful.


Our approach
============

Boogie tends to favor more functional approaches than Django. While we like
the function view contract, we recognize that classes are very good to compose
isolated namespaces, specially in an object-oriented language like Python. That
said, we introduce a different approach to class-based views, one that opts for
simplicity:

.. important::

    A view instance is a callable object that obeys Django's view function
    contract.

Boogie's base :class:`boogie.View` class offers a few goodies. First, it
understands the presence of separate get, post, delete, etc methods and
redirect control flow to the appropriate handler when a request is made:

.. code-block:: python

    from boogie.views import View

    # on view.py
    class FormView(View):
        # Only called when request.method == 'GET'
        def get(self, request):
            ctx = {'form': MyForm()}
            return render(request, 'my-template.html', ctx)

        # Called when request.method == 'POST'
        def post(self, request):
            form = MyForm(request.POST)
            ctx = {'form': form}
            if form.is_valid():
                return redirect('success/')
            else:
                return render(request, 'my-template.html', ctx)

    # on urls.py
    urlpatterns = [
        ...,
        path('post/', FormView()),
    ]



