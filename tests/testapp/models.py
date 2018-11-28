from django.utils.timezone import now

from boogie import models
from boogie.models import F
from boogie.rest import rest_api


class Gender(models.IntEnum):
    MALE = 'male'
    FEMALE = 'female'


@rest_api(exclude=['created', 'modified'])
class User(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField(blank=True, null=True)
    created = models.DateTimeField(default=now)
    modified = models.DateTimeField(auto_now=True)
    gender = models.EnumField(Gender, blank=True, null=True)

    __str__ = (lambda self: self.name)


@rest_api()
class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.title} ({self.author})'


@models.queryset_method(Book)
def at_beginning(qs):
    return qs.filter(title__startswith='a')


@rest_api.list_action(Book, name='at_beginning')
def at_beginning_action():
    return Book.objects.at_beginning()


@models.queryset_method(Book)
def long_title(qs):
    return qs.filter(F('title').length() >= 10)


@rest_api.list_action(Book)
def long_titles():
    return Book.objects.long_title()


@rest_api.detail_action(Book)
def upper_title(book):
    return book.title.upper()
