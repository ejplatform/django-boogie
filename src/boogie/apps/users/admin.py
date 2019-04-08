from copy import deepcopy

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin

from . import models


@admin.register(models.User)
class UserAdmin(AuthUserAdmin):
    # Remove "first_name" and "last_name" and replace it by "name"
    fieldsets = list(deepcopy(AuthUserAdmin.fieldsets))
    fieldsets[1][1]["fields"] = ("name", "email")
    fieldsets = tuple(fieldsets)
