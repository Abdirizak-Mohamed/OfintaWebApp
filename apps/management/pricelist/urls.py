# django
from django.urls import path

# ofinta
from apps.management.pricelist.views import PriceList, \
    PriceListItemDelete, PriceListInactive, PriceListItemAdd, \
    PriceListItemEdit, AddPositionFromItem, PriceListItemSearch

urlpatterns = [
    path('', PriceList.as_view(), name='pricelist'),
    path('history/', PriceListInactive.as_view(), name='pricelist-inactive'),
    path(
        '<int:pk>/delete/',
        PriceListItemDelete.as_view(),
        name='pricelist-item-delete'
    ),

    # ajax patterns
    path(
        'add_item/',
        PriceListItemAdd.as_view(),
        name='pricelist-item-add'
    ),
    path(
        '<int:pk>/edit_item/',
        PriceListItemEdit.as_view(),
        name='pricelist-item-edit'
    ),
    path(
        '<int:pk>/add_position/',
        AddPositionFromItem.as_view(),
        name='add-position-from-item'
    ),
    path(
        'search/',
        PriceListItemSearch.as_view(),
        name='pricelist-item-search'
    ),
]
