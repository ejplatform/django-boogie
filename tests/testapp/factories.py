from django.utils.timezone import now, timedelta

from .models import User, Book


def author():
    return User.objects.create(name='Author')


def young_author():
    return User.objects.create(name='Young', age=18)


def old_author():
    return User.objects.create(name='Old', age=80,
                               created=now() - timedelta(days=-1))


def book():
    return Book.objects.create(title='Book', author=author())


def authors():
    author()
    young_author()
    old_author()
    return User.objects


def books():
    return library()[1]


def library():
    book()

    young = young_author()
    Book.objects.create(title='First Kindle', author=young)
    Book.objects.create(title='Second Kindle', author=young)

    old = old_author()
    Book.objects.create(title='First Book', author=old)
    Book.objects.create(title='Second Book', author=old)

    return User.objects, Book.objects
