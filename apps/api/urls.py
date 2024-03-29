# django
from django.urls import re_path, include

urlpatterns = [
    re_path(r'^', include(('apps.api.v1.urls', 'default'), namespace='default')),
    re_path(r'^v1/', include(('apps.api.v1.urls', 'v1'), namespace='v1')),
]