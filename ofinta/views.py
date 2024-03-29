# system
import json
import logging

# django
from django.conf import settings
from django.contrib.auth.views import LoginView
from django.http.response import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import RedirectView

# third party
from rest_framework import parsers, renderers
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.response import Response
from rest_framework.views import APIView

# ofinta
from apps.core.models import UserRoles
from apps.management.orders.constants import OrderStatus, PushStatuses
from apps.management.orders.models import Payment, Order
from apps.mpesa_gateway.models import MPesaTransaction
from apps.mpesa_gateway.utils import process_success_webhook

from .forms import LoginForm

logger = logging.getLogger(__name__)


class OfintaLoginView(LoginView):
    template_name = 'login.html'
    form_class = LoginForm

    def get_success_url(self):
        """
        Generate url to redirect to after login in depending on the user role
        :return: url
        """
        user = self.request.user
        if user.role == UserRoles.ADMINISTRATOR:
            return reverse('administration:dashboard')
        else:
            return reverse('management:dashboard')


class DashboardView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user
        if user.is_owner or user.is_manager:
            return reverse('management:dashboard')
        elif user.is_admin:
            return reverse('administration:dashboard')
        else:
            return reverse('login')


@csrf_exempt
def mpesa_result(request):
    request_json = json.loads(request.body or '{}')
    response_json, response_status_code = process_success_webhook(request_json)
    return JsonResponse(response_json, status=response_status_code)


@csrf_exempt
def mpesa_timeout(request):
    """
    For now request data is unknown
    :param request:
    :return:
    """
    JsonResponse({})


def get_transaction_status(request, order_id):
    order = Order.objects.get(id=order_id)
    payment = order.payment
    txn = payment.transaction
    txn.check_timeout()
    return JsonResponse({'status': txn.status_verbose})


class ObtainAuthToken(APIView):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = AuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        
        data = {'token': token.key, 'user': user.id}
        
        if not user.changed_password:
            data.update({ 'changed_password': False })
        
        return Response(data)


obtain_auth_token = ObtainAuthToken.as_view()
