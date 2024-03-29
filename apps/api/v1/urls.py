# third party
from django.urls import re_path, include
from push_notifications.api.rest_framework import APNSDeviceAuthorizedViewSet, \
    GCMDeviceAuthorizedViewSet
from rest_framework import routers

# ofinta
from apps.api.v1.views import OrdersViewSet, DriverLocationViewSet, \
    DriverOrdersViewSet, ChangePasswordView, RestorePasswordRequestView, \
    RestorePasswordSubmitView, MessageView, DriverProfileViewSet, \
    UnregisterDeviceView

router = routers.DefaultRouter()
router.register(r'orders', OrdersViewSet)
router.register(r'device/apns', APNSDeviceAuthorizedViewSet)
router.register(r'device/gcm', GCMDeviceAuthorizedViewSet)


drivers_urls = [
    re_path(
        r'^profile/$',
        DriverProfileViewSet.as_view(
            {'get': 'retrieve', 'patch': 'partial_update'}
        ),
        name='driver-profile'
    ),
    re_path(
        r'^location/$',
        DriverLocationViewSet.as_view({'patch': 'update'}),
        name='driver-location'
    ),
    re_path(
        r'^order/(?P<pk>[^/.]+)/accept/$',
        DriverOrdersViewSet.as_view({'post': 'accept'}),
        name='accept-order'
    ),
    re_path(
        r'^order/(?P<pk>[^/.]+)/skip/$',
        DriverOrdersViewSet.as_view({'post': 'skip'}),
        name='skip-order'
    ),
    re_path(
        r'^order/(?P<pk>[^/.]+)/confirm/$',
        DriverOrdersViewSet.as_view({'patch': 'confirm'}),
        name='confirm-order'
    ),
    re_path(
        r'^order/(?P<pk>[^/.]+)/pay/$',
        DriverOrdersViewSet.as_view({'post': 'pay'}),
        name='pay-order'
    ),
    re_path(
        r'^orders/$',
        DriverOrdersViewSet.as_view({'get': 'active_list'}),
        name='driver-orders-active'
    ),
    re_path(
        r'^orders/history/$',
        DriverOrdersViewSet.as_view({'get': 'history_list'}),
        name='driver-orders-history'
    ),
    re_path(
        r'^orders/(?P<pk>[^/.]+)/$',
        DriverOrdersViewSet.as_view(
            {'get': 'retrieve', 'patch': 'partial_update'}
        ),
        name='driver-order'
    )
]


password_urls = [
    re_path(
        r'^change_password/$',
        ChangePasswordView.as_view(),
        name='change-password'
    ),
    re_path(
        r'^restore_password_request/$',
        RestorePasswordRequestView.as_view(),
        name='restore-password-request'
    ),
    re_path(
        r'^restore_password_submit/$',
        RestorePasswordSubmitView.as_view(),
        name='restore-password-submit'
    ),
]


chat_urls = [
    re_path(
        r'^$',
        MessageView.as_view({'get': 'list', 'post': 'create'}),
        name='chat'
    ),
]

urlpatterns = [
    re_path(r'^', include(router.urls)),
    re_path(r'^driver/', include(drivers_urls)),
    re_path(r'^password/', include(password_urls)),
    re_path(r'^chat/', include(chat_urls)),
    re_path(
        r'^unregister-device$',
        UnregisterDeviceView.as_view(),
        name='^unregister-device'
    ),
]
