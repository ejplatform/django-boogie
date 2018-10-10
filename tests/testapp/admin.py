from django.contrib.admin import site

from . import models

site.register(models.User)
site.register(models.Book)
