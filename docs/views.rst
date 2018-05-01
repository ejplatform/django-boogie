=================
Class based views
=================

Old Django introduced generic function-based views. While those views were
convenient, the original implementation lacks composability: function-based
generic views implement common usage patterns, but were hard to modify and
reuse code across implementations. Now, Django introduced class-based views
to solve those problems. The new implementation, however, has its own set
of flaws: it is based on a very confusing inheritance tree [#link], and it
uses a confusing API .

* It is not clear what is a View object: instances are never used directly
  and the API expect to be used via the View.as_view() class method.
* Data flow is unclear. In most generic views, the request, *args and **kwargs
  are saved as attributes and are often also passed as argument of many
  internal methods. You never know when, at least Django documentation is very
  good ;)
* They are very stateful objects. Some people may find it distasteful.


Our approach
============

Boogie tends to favor more functional approaches than what Django provides.
While we like the function view contract, we recognize that classes are very
good to compose isolated namespaces. We introduce a different approach to
class-based views. We opt for simplicity:

.. important::

     A view instance is a callable object that obeys Django's view function
    contract.

We provide a base-class implementation with a few goodies. The first is that it
understands the presence of separate get, post, delete, etc methods and may direct
the flow to those methods:

.. code-block::

    from boogie.views import View

    # on view.py
    class FormView(View):
        def get(self, request):
            ctx = {'form': MyForm()}
            return render(request, 'my-template.html', ctx)

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



