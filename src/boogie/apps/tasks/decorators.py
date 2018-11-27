from celery import shared_task
from django.core.exceptions import ImproperlyConfigured

from .settings import REGISTERED_FUNCTIONS


def task_method(func):
    """
    Register method as a task.
    """
    func.is_task = True
    func.is_method = True
    return func


def task(cls, name=None, function=None):
    """
    Register a handler function that executes a task.

    Each task should be associated with a Job class.
    """
    if not isinstance(cls, type):
        raise ImproperlyConfigured(
            'Job class is missing as decorator argument. Please fix your '
            'decorator to be like @task(JobClass)'
        )
    if function is None:
        return lambda function: task(cls, name, function) or function

    name = name or function.__name__
    task_name = f'{cls.__module__}.{cls.__name__}:{name}'

    def call(object, *args, **kwargs):
        return cls.objects.call(name, object, *args, **kwargs)

    def delayed(object, *args, **kwargs):
        return cls.objects.delayed(name, object, *args, **kwargs)

    def schedule(object, *args, **kwargs):
        return cls.objects.schedule(name, object, *args, **kwargs)

    @shared_task(name=task_name)
    def celery_task(task_id):
        task = cls.objects.get(id=task_id)
        return task.run(is_async=False)

    function.task_name = task_name
    function.call = call
    function.delayed = delayed
    function.schedule = schedule
    function.celery_runner = celery_task

    REGISTERED_FUNCTIONS[cls, name] = {
        'function': function,
        'is_method': getattr(function, 'is_method', False),
    }
