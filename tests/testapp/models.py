from django.db import models as dj_models
from django.utils.timezone import now

from boogie import models
from boogie.rest import rest_api


class Gender(models.IntEnum):
    MALE = 'male'
    FEMALE = 'female'


@rest_api(exclude=['created', 'modified'])
class User(dj_models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField(blank=True, null=True)
    created = models.DateTimeField(default=now)
    modified = models.DateTimeField(auto_now=True)
    gender = models.EnumField(Gender, blank=True, null=True)
    objects = models.Manager()

    __str__ = lambda self: self.name


@rest_api()
class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
