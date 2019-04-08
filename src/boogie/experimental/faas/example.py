import os

from django import setup
from django.core.handlers.wsgi import WSGIHandler


class FaaS:
    """
    Base class for FaaS applications.
    """

    @classmethod
    def from_settings(cls, settings, **kwargs):
        function = cls(settings, **kwargs)
        function.init()
        return function

    def __init__(self, settings, methods=None):
        self.settings = settings
        self.wsgi = None

    def init(self):
        """
        Start Django project.
        """
        os.environ["DJANGO_SETTINGS_MODULE"] = self.settings
        setup()
        self.wsgi = WSGIHandler()

    def request(self, url, **kwargs):
        request = self.make_request(url, **kwargs)
        print(request)
        self.wsgi()


#
# example
#
# function = FaaS.from_settings("tests.testproject.settings")
# print(function.request("?api/v1/"))
# print(function.request("?api/v1/"))
