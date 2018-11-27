import functools
from time import sleep

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
from model_utils import Choices
from model_utils.models import StatusModel, TimeStampedModel

from boogie.apps.tasks.manager import TaskQuerySet
from boogie.apps.tasks.settings import REGISTERED_FUNCTIONS, USE_CELERY, log


class TaskMeta(type(models.Model)):
    """
    Metaclass that register @task-decorated methods as tasks.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self._meta.abstract:
            for attr in dir(self):
                method = getattr(self, attr, None)
                if getattr(method, 'is_task', False):
                    self.register(name=attr, function=method)


class Task(StatusModel, TimeStampedModel, metaclass=TaskMeta):
    """
    Represents a deferred computation.

    Concrete classes should override the object and result fields.
    """
    STATUS = Choices(
        ('pending', _('pending')),
        ('running', _('running')),
        ('finished', _('finished')),
        ('skipped', _('skipped')),
        ('failed', _('failed')),
    )
    function = models.CharField(max_length=40)
    arguments = JSONField(default=dict)
    object = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE)
    result = models.TextField(blank=True)

    is_pending = property(lambda self: self.status == self.STATUS.pending)
    is_running = property(lambda self: self.status == self.STATUS.running)
    is_finished = property(lambda self: self.status == self.STATUS.finished)
    is_skipped = property(lambda self: self.status == self.STATUS.skipped)
    is_failed = property(lambda self: self.status == self.STATUS.failed)

    objects = TaskQuerySet.as_manager()

    class Meta:
        abstract = True

    class Skip(Exception):
        """
        Exception raised when task should be skipped
        """

    @classmethod
    def get_object_model(cls):
        """
        Return model class for the object field.
        """
        field = cls._meta.get_field('object')
        return field.remote_field.model

    @classmethod
    def _create(cls, **kwargs):
        # This function was separated to be mocked in tests
        return cls.objects.create(**kwargs)

    @classmethod
    def _create_no_db(cls, **kwargs):
        idx = getattr(cls, '_no_db_index', 1) + 1
        return cls(id=idx, **kwargs)

    #
    # Instance methods
    #
    def __str__(self):
        class_name = type(self.object).__name__
        obj_data = f'{class_name}(id={self.object.id})'
        args = self.arguments.get('args', ())
        kwargs = self.arguments.get('kwargs', {})
        kwargs_data = (f'{key}={repr(value)}' for key, value in kwargs)
        args_data = ', '.join([obj_data, *args, *kwargs_data])
        return f'{self.function} ({self.status}): {args_data}'

    def wrap_result(self, result):
        """
        Convert result value into a raw valid database representation.

        The resulting value should be safe to store in the .result attribute.
        """
        return result

    def unwrap_result(self, raw):
        """
        Convert raw result value into a valid Python representation
        """
        return raw

    def set_args(self, obj, *args, **kwargs):
        """
        Sets arguments of the task function.
        """
        self.object = obj
        self.arguments = {'args': args, 'kwargs': kwargs}

    def call(self, *args, **kwargs):
        """
        Set object and extra arguments and run task in the foreground.
        """
        self.set_args(*args, **kwargs)
        return self.execute()

    def call_background(self, *args, **kwargs):
        """
        Set object and arguments and run task in the background.
        """
        self.set_args(*args, **kwargs)
        self.execute_background()
        return self

    def run(self, is_async=True):
        """
        Runs task, if necessary and fetch result.
        """
        if self.is_finished:
            return self if is_async else self.unwrap_result(self.result)
        elif self.is_pending:
            return self._run_pending(is_async)
        elif is_async:
            return self
        elif self.is_running:
            return self._wait_completion()
        elif self.is_failed:
            raise RuntimeError('task failed to complete')
        else:
            return None

    def _run_pending(self, is_async):
        if is_async:
            self.execute_background()
            return self
        else:
            result = self.execute()
            if self.is_failed:
                return self.run(is_async=False)
            return result

    def _wait_completion(self):
        dt = 0.01
        for __ in range(int(10 / dt)):
            sleep(dt)
            if not self.is_running:
                return self.run(is_async=False)
        raise TimeoutError('timeout while waiting for task completion')

    def execute(self, commit=True):
        """
        Run task synchronously and return the result.
        """

        self.status = self.STATUS.running
        if commit:
            self.save(update_fields=['status'])

        # Compute result
        result = None
        try:
            result = self.execute_function()
            log.info(f'task {self} successfully executed')
        except self.Skip:
            self.status = self.STATUS.skipped
            log.info(f'task skipped: {self}')
        except Exception as exc:
            self.status = self.STATUS.failed
            log.warning(f'error running task ({self}): {exc}')
        else:
            self.result = self.wrap_result(result)
            self.status = self.STATUS.finished
        if commit:
            self.save()
        return result

    def execute_background(self):
        """
        Schedule task to run in the background using celery.
        """
        task = self._get_handler(self.function).task

        if USE_CELERY:
            return task.delay(self.id)
        else:
            return task.apply([self.id])

    def execute_function(self):
        """
        Execute handler function and return its result.

        This function does not update the Task object.
        """
        args = self.arguments.get('args', ())
        kwargs = self.arguments.get('kwargs', {})
        function = self._get_handler(self.function).runner

        if self.get_object_model() == ContentType:
            object_id = kwargs.pop('object_id')
            model = self.object.model_class()
            object = model.objects.get(id=object_id)
        else:
            object = self.object

        return function(object, *args, **kwargs)

    def _get_handler(self, name):
        """
        Register a handler for some pair of (TaskClass, HandlerName).

        Handler names of a given task class are unique.
        """
        info = REGISTERED_FUNCTIONS[type(self), name]
        function = info['function']
        is_method = info['is_method']
        if is_method:
            return functools.partial(function, self)
        return function


class JsonTask(Task):
    """
    Special task that expect JSON results.
    """

    def wrap_result(self, result):
        import json

        return json.dumps(result)

    def unwrap_result(self, raw):
        import json

        return json.loads(raw)


class AbstractPandasTask(Task):
    """
    Abstract model for tasks that result in Pandas DataFrames.
    """
    result = models.BinaryField(blank=True)

    def wrap_result(self, result):
        try:
            return result.to_msgpack()
        except AttributeError:
            cls_name = result.__class__.__name__
            raise TypeError(f'result must be a DataFrame, got {cls_name}')

    def unwrap_result(self, raw):
        import pandas as pd

        return pd.read_msgpack(raw)

    class Meta:
        abstract = True
