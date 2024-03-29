# django
from django.urls import path

# ofinta
from apps.demoshop.views import Demoshop


urlpatterns = [
    path('', Demoshop.as_view(), name='demoshop'),
]
