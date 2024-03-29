# django
from django.urls import path

# ofinta
from apps.administration.admin_accounts.views import AdminAccountDetails, \
    AdminAccountEdit, AdminAccountBlock, AdminAccountRemove, AdminAccountsList, \
    AdminAccountAdd
from apps.administration.shop_accounts.views import ShopAccountRemove, \
    ShopAccountBlock, ShopAccountEdit, ShopAccountDetails, ShopAccountAdd, \
    ShopAccountsList

urlpatterns = [
    path('', AdminAccountsList.as_view(), name='admin-accounts-list'),
    path('add/', AdminAccountAdd.as_view(), name='admin-account-add'),
    path(
        '<int:pk>/',
        AdminAccountDetails.as_view(),
        name='admin-account-details'
    ),
    path(
        '<int:pk>/edit/',
        AdminAccountEdit.as_view(),
        name='admin-account-edit'
    ),
    path(
        '<int:pk>/block/',
        AdminAccountBlock.as_view(),
        name='admin-account-disable'
    ),
    path(
        '<int:pk>/remove/',
        AdminAccountRemove.as_view(),
        name='admin-account-remove'
    ),
]
