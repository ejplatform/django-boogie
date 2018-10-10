from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include

from boogie.rest import rest_api

urlpatterns = [
    path('api/', include(rest_api.urls)),
    path('admin/', admin.site.urls),
]
urlpatterns.extend(staticfiles_urlpatterns())
