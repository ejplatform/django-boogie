class Db:
    """
    Provides easy access to model tables.
    """

    def __init__(self, app=None):
        self._app = app

    def __getattr__(self, attr):
        if self._app is None:
            return Db(attr)
        else:
            from django.apps import apps

            model = apps.get_model(self._app, attr)
            return wrap_as_boogie_manager(model._default_manager)


db = Db()


def wrap_as_boogie_manager(manager):
    """
    Wraps a manager instance as a Boogie-compatible manager.
    """
    # TODO
    return manager
