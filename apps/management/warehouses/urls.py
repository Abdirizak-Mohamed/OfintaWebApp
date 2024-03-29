# django
from django.urls import path

# ofinta
from apps.management.orders.views import OrdersList, OrderDetails, OrderEdit, \
    OrderCancel, OrdersHistory
from apps.management.warehouses.views import WarehousesList, WarehouseAdd, \
    WarehouseDetails, WarehouseEdit

urlpatterns = [
    path('', WarehousesList.as_view(), name='warehouses-list'),
    path('add/', WarehouseAdd.as_view(), name='warehouse-add'),
    path('<int:pk>/', WarehouseDetails.as_view(), name='warehouse-details'),
    path('<int:pk>/edit/', WarehouseEdit.as_view(), name='warehouse-edit'),
]
