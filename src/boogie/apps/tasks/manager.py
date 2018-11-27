from django.contrib.contenttypes.models import ContentType
from django.db import models

from .tasks import get_functions


class TaskQuerySet(models.QuerySet):

    def last_task(self, function):
        """
        Return the last task for function
        """
        return self.filter(function=function).order_by('created').last()

    def clean_tasks(self, function, keep_last=True):
        """
        Remove old tasks for the given function.
        """
        qs = self.filter(function=function)
        if keep_last:
            qs.exclude(id=self.last_task(function).id)
        return qs.delete()

    def clean_all_tasks(self, keep_last=True):
        """
        Clean all tasks for all functions.
        """
        if keep_last:
            cls = self.model.get_object_model()
            last_tasks = [self.last_task(f).id for f in get_functions(cls)]
            return self.exclude(id__in=last_tasks).delete()
        else:
            return self.all().delete()


class TaskManager(TaskQuerySet.as_manager()):
    def create_delayed(self, function, obj, *args, **kwargs):
        """
        Creates a new promise and return it.

        Return a promise.
        """
        if self.model.get_object_model() == ContentType:
            kwargs['object_id'] = obj.id
            obj = ContentType.objects.get_for_model(type(obj))
        arguments = {'args': args, 'kwargs': kwargs}
        create = self.model._create
        return create(function=function, arguments=arguments, object=obj)

    def create_scheduled(self, function, obj, *args, **kwargs):
        """
        Similar to call(), but schedule job to run in the background using
        celery.
        """
        task = self.create_delayed(function, obj, *args, **kwargs)
        task.run(is_async=True)
        return task

    def call(self, function, obj, *args, **kwargs):
        """
        Creates a new promise and immediately execute it.

        Return the result synchronously.
        """
        task = self.create_delayed(function, obj, *args, **kwargs)
        return task.run(is_async=False)
