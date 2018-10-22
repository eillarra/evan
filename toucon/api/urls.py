from django.conf.urls import include, url
from rest_framework.documentation import include_docs_urls

from .routers import Router


urlpatterns = [
    url(r'^v1/', include((Router('v1').urls, 'api'), namespace='v1')),
    url(r'^', include_docs_urls(title='Toucon API')),
]
