==========
Job runner
==========

Celery is a great task runner and takes care of many issues inherent to running
asynchronous tasks in distributed systems.


.. code-block:: python

    @job()
    def process_data(object: Foo, n_iter=100):
        ...



    process_data.create()

