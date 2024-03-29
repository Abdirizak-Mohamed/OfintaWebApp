# django
from django.urls import path

# ofinta
from apps.management.dashboard.views import DashboardView


urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
]
