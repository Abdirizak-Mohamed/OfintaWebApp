# django
from django.urls import path

# ofinta
from apps.administration.dashboard.views import DashboardView


urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
]
