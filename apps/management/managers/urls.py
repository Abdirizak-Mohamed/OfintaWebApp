# django
from django.urls import path

# ofinta
from apps.management.managers.views import ManagersList, ManagerAdd, \
    ManagerDetails, ManagerEdit, ManagerStatus, ManagerRemove


urlpatterns = [
    path('', ManagersList.as_view(), name='managers-list'),
    path('add/', ManagerAdd.as_view(), name='manager-add'),
    path('<int:pk>/', ManagerDetails.as_view(), name='manager-details'),
    path('<int:pk>/edit/', ManagerEdit.as_view(), name='manager-edit'),
    path(
        '<int:pk>/status/',
        ManagerStatus.as_view(),
        name='manager-status'
    ),
    path(
        '<int:pk>/remove/',
        ManagerRemove.as_view(),
        name='manager-remove'
    ),
]
