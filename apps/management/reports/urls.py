# django
from django.urls import path

# ofinta
from apps.management.reports.views import Reports


urlpatterns = [
    path('', Reports.as_view(), name='reports'),
]
