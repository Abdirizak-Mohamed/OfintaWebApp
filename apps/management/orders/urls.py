# django
from django.urls import path

# ofinta
from apps.management.orders.views import OrdersList, OrderDetails, OrderEdit, \
    OrderCancel, OrdersHistory, DriverAssign, PaymentLinkCreate


urlpatterns = [
    path('', OrdersList.as_view(), name='orders-list'),
    path('create/', PaymentLinkCreate.as_view(), name='payment-link-create'),
    path('history/', OrdersHistory.as_view(), name='orders-history'),
    path('<int:pk>/', OrderDetails.as_view(), name='order-details'),
    path('<int:pk>/edit/', OrderEdit.as_view(), name='order-edit'),
    path(
        '<int:pk>/assign_driver/',
        DriverAssign.as_view(),
        name='driver-assign'
    ),
    path('<int:pk>/cancel/', OrderCancel.as_view(), name='order-cancel'),
]
