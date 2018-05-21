=================
boogie.apps.tasks
=================

Boogie tasks app provides integration with celery to run tasks in the background
and store results to the database. It aims to have a straightforward interface
that we can easily use to register new tasks and run operations on the
background.

For simple uses, we can simply decorate a function with the task decorator
and it will expose additional methods for delayed computation. Every Boogie
task expects a django model instance as the first argument. By default, it
should return JSON compatible data.

.. code-block:: python

    from boogie.apps.tasks import task

    @task
    def clean_user_posts(user, force=False):
        removed_posts = user.posts.delete(force=force)
        return {
            'user': user.username,
            'removed': removed_posts,
        }


The decorated function gains some special methods to perform delayed execution:


``task_func(obj, *args, **kwargs)``:
    Simply call the function. Do not create any task instance in the database
    or trigger special behavior.

``task_func.call(obj, *args, **kwargs)``:
    Create a Task instance and call it synchronously. This will save the result
    in the database. Return the result of the task function.

``task_func.delayed(obj, *args, **kwargs)``:
    Return a new task instance. This method triggers the task function and runs
    it on the background.

``task_func.paused(obj, *args, **kwargs)``:
    Return a new paused task instance. This method does not trigger the
    execution of the task function. User should trigger its run() method
    manually.

``task_func.schedule(time, obj, *args, **kwargs)``:
    Schedule task to start on the specified time. Return a task object. If time
    is a number, it is interpreted as a time delta (in seconds) from current
    time.

The task function also receives the following methods to manage executing
tasks.

``task_func.results(obj=None)``:
    Return all results from task. May filter by object.

``task_func.tasks(obj=None)``:
    Return a queryset with all task objects for the given task.

``task_func.finished(obj=None)``:
    Return all finished tasks.

``task_func.clean(obj=None, keep_last=False, finished=True)``:
    Clean all task results.



==============
Advanced usage
==============