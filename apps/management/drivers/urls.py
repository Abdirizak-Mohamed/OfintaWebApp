# django
from django.urls import path

# third party
from rest_framework.authtoken.views import ObtainAuthToken

# ofinta
from apps.api.v1.serializers import DriverAuthTokenSerializer
from apps.management.drivers.views import DriversList, DriverDetails, \
    DriverEdit, DriverStatus, DriverAdd


urlpatterns = [
    path('', DriversList.as_view(), name='drivers-list'),
    path('add/', DriverAdd.as_view(), name='driver-add'),
    path('<int:pk>/', DriverDetails.as_view(), name='driver-details'),
    path('<int:pk>/edit/', DriverEdit.as_view(), name='driver-edit'),
    path(
        '<int:pk>/status/',
        DriverStatus.as_view(),
        name='driver-status'
    ),
    path(
        'login/',
        ObtainAuthToken.as_view(serializer_class=DriverAuthTokenSerializer),
        name='driver-login'
    ),
]
