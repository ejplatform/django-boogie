class Db:
    """
    Provides easy access to model tables.
    """

    def __init__(self, app=None):
        self._app = app

    def __getattr__(self, attr):
        if self._app is None:
            return Db(attr)
        elif attr.endswith("_model"):
            from django.apps import apps

            return apps.get_model(self._app, attr[:-6])
        elif attr.endswith("_objects"):
            from django.apps import apps

            model = apps.get_model(self._app, attr[:-8])
            return wrap_as_boogie_manager(model._default_manager)
        elif attr.endswith("s"):
            return self.__getattr__(attr[:-1] + "_objects")


db = Db()


def wrap_as_boogie_manager(manager):
    """
    Wraps a manager instance as a Boogie-compatible manager.
    """
    # TODO
    return manager
