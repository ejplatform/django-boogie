from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include

from boogie.rest import rest_api

urlpatterns = [
    #path('api/v1/', include(rest_api.get_urls('v1'))),
    path('api/', include(rest_api.urls)),
]
urlpatterns.extend(staticfiles_urlpatterns())
