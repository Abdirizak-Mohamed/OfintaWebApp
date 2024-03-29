# django
from django.urls import path

# ofinta
from apps.administration.shop_accounts.views import ShopAccountRemove, \
    ShopAccountBlock, ShopAccountEdit, ShopAccountDetails, ShopAccountAdd, \
    ShopAccountsList

urlpatterns = [
    path('', ShopAccountsList.as_view(), name='shop-accounts-list'),
    path('add/', ShopAccountAdd.as_view(), name='shop-account-add'),
    path(
        '<int:pk>/',
        ShopAccountDetails.as_view(),
        name='shop-account-details'
    ),
    path(
        '<int:pk>/edit/',
        ShopAccountEdit.as_view(),
        name='shop-account-edit'
    ),
    path(
        '<int:pk>/block/',
        ShopAccountBlock.as_view(),
        name='shop-account-disable'
    ),
    path(
        '<int:pk>/remove/',
        ShopAccountRemove.as_view(),
        name='shop-account-remove'
    ),
]
