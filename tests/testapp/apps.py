from django.apps import AppConfig


class TestappConfig(AppConfig):
    name = 'tests.testapp'
    api = None

    def ready(self):
        from . import api
        self.api = api
