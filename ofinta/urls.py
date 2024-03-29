# django
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path, include, reverse_lazy, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import TemplateView

# ofinta
from apps.management.orders.views import PaymentLinksList, PaymentLinkDetails, \
    PaymentLinkEdit, PaymentLinkStep1, PaymentLinkStep2, PaymentLinkCancel
from ofinta.views import OfintaLoginView, DashboardView, \
    obtain_auth_token, mpesa_result, mpesa_timeout, get_transaction_status

urlpatterns = [
    path('admin/', admin.site.urls),
    path('impersonate/', include('impersonate.urls')),
    path('api/', include(('apps.api.urls', 'api'), namespace='api')),
    path(
        '',
        OfintaLoginView.as_view(redirect_authenticated_user=True),
        name='login'
    ),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    
    path('not_authorized/', TemplateView.as_view(template_name='not_authorized.html', content_type='text/html'), name='not_authorized'),

    path(
        'logout/',
        LogoutView.as_view(next_page=reverse_lazy('login')),
        name='logout'
    ),
    path(
        'management/',
        include(
            ('apps.management.urls', 'management'),
            namespace='management'
        )
    ),
    path(
        'administration/',
        include(
            ('apps.administration.urls', 'administration'),
            namespace='administration')
    ),
    path(
        'demoshop/',
        include(
            ('apps.demoshop.urls', 'demoshop'),
            namespace='demoshop'
        )
    ),

    # payment links
    path(
        'orders/<str:slug>/',
        PaymentLinkEdit.as_view(),
        name='payment-link-edit'
    ),
    path(
        'orders/<str:slug>/cancel',
        PaymentLinkCancel.as_view(),
        name='payment-link-cancel'
    ),
    path(
        'orders/<str:slug>/success',
        PaymentLinkStep1.as_view(),
        name='payment-link-success'
    ),
    path(
        'orders/<str:slug>/paid',
        PaymentLinkStep2.as_view(),
        name='payment-link-paid'
    ),

    # mpesa callbacks
    path('mpesa-result/', mpesa_result, name='mpesa-result'),
    path('mpesa-timeout/', mpesa_timeout, name='mpesa-timeout'),

    path(
        'transaction/<int:order_id>/status/',
        get_transaction_status,
        name='get_transaction_status'
    ),
    path('api-token-auth/', obtain_auth_token, name='api-auth'),

    re_path(r'^select2/', include('django_select2.urls')),
    re_path(r'^upload/', include('django_file_form.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
