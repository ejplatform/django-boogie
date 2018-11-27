from boogie.apps.tasks.settings import REGISTERED_FUNCTIONS


class TaskProperty:
    """
    Implements the Task.task.<method> interface.
    """

    def __init__(self, cls):
        self._cls = cls

    def __call__(self, func=None, **kwargs):
        if func is None:
            return lambda func: self(func, **kwargs)

        raise NotImplementedError

    def __getattr__(self, attr):
        funcs = get_functions(self._cls)
        try:
            return funcs[attr]
        except KeyError:
            raise AttributeError(f'function not registerd: {attr}')


class TaskPropertyDescriptor:
    def __get__(self, instance, owner=None):
        if instance is not None:
            raise ValueError(
                'task attribute cannot be accessed from task instances'
            )
        return TaskProperty(owner)


def get_functions(cls):
    items = REGISTERED_FUNCTIONS
    return {f for cls_, f in items if cls is cls_}