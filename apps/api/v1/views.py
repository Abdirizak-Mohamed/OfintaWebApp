# system
import os
import binascii

# django
from django.conf import settings
from django.core.mail import send_mail

# third party
from django.shortcuts import get_object_or_404
from push_notifications.models import GCMDevice
from rest_framework import mixins, status
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

# ofinta
from apps.api.v1.serializers import OrderSerializer, DriverLocationSerializer, \
    ChangePasswordSerializer, RestorePasswordRequestSerialzier, \
    RestorePasswordSubmitSerialzier, MessageSerializer, OrderConfirmSerializer, \
    DriverProfileSerializer, OfintaUserSerializer
from apps.core.models import OfintaUser
from apps.management.chat.models import Message
from apps.management.drivers.models import DriverProfile
from apps.management.orders.constants import OrderStatus, OrderAssignmentStatus, \
    PaymentMethod
from apps.management.orders.models import Order, OrderAssignments, Payment


class OrdersViewSet(mixins.CreateModelMixin,
                    GenericViewSet):
    """
    Orders API endpoint viewset
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        shop = self.request.user.shop
        queryset = shop.get_orders()
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            if is_active == 'True':
                queryset = queryset.get_open()
            elif is_active == 'False':
                queryset = queryset.get_recent()

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        else:
            return Response(
                serializer.error_codes,
                status=status.HTTP_400_BAD_REQUEST
            )


class DriverOrdersViewSet(mixins.RetrieveModelMixin,
                          mixins.ListModelMixin,
                          mixins.UpdateModelMixin,
                          GenericViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def active_list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset(is_active=True))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def history_list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset(is_active=False))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self, is_active=None):
        shop = self.request.user.shop
        queryset = shop.get_orders()
        driver_assignments = OrderAssignments.objects.filter(
            driver=self.request.user
        )

        if is_active is None:
            return queryset

        orders_pks = []
        orders = queryset.filter(
            pk__in=driver_assignments.values_list('order', flat=True)
        )

        if is_active or is_active is None:
            for order in orders:
                last_assignment = driver_assignments.filter(order=order).last()
                if not last_assignment:
                    continue

                if last_assignment.status == OrderAssignmentStatus.REJECTED:
                    continue

                orders_pks.append(order.pk)
        else:
            for order in orders:
                last_assignment = driver_assignments.filter(order=order).last()
                if not last_assignment:
                    continue

                if last_assignment.status != OrderAssignmentStatus.ACCEPTED:
                    continue

                orders_pks.append(order.pk)

        queryset = queryset.filter(pk__in=orders_pks)

        if is_active:
            queryset = queryset.get_open()
        else:
            queryset = queryset.get_recent()

        return queryset

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)

            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}

            return Response(serializer.data)
        else:
            return Response(
                serializer.error_codes,
                status=status.HTTP_400_BAD_REQUEST
            )

    def accept(self, request, *args, **kwargs):
        order = self.get_object()
        response_data = {}
        if order.status == OrderStatus.ASSIGNED:
            assignments = order.assignments.filter(
                driver=self.request.user
            )
            if not assignments.exists():
                response_data["message"] = "This order is not assigned to you"
                return Response(
                    data=response_data,
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                assignment = assignments.last()
                assignment.status = OrderAssignmentStatus.ACCEPTED
                assignment.save()

                order.driver = self.request.user
                order.status = OrderStatus.ACCEPTED
                order.save()
                response_data["message"] = "Order accepted"
                return Response(
                    data=response_data,
                    status=status.HTTP_200_OK
                )
        else:
            response_data = {
                "message": "Current order cannot be accepted at the moment"
            }
            return Response(
                data=response_data,
                status=status.HTTP_400_BAD_REQUEST
            )

    def skip(self, request, *args, **kwargs):
        order = self.get_object()
        response_data = {}
        if order.status == OrderStatus.ASSIGNED:
            assignments = order.assignments.filter(
                driver=self.request.user
            )
            if not assignments.exists():
                response_data["message"] = "This order is not assigned to you"
                return Response(
                    data=response_data,
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                assignment = assignments.last()
                assignment.status = OrderAssignmentStatus.REJECTED
                assignment.save()

                order.status = OrderStatus.NEW
                order.driver = None
                order.save()
                response_data["message"] = "Order skipped"
                return Response(
                    data=response_data,
                    status=status.HTTP_200_OK
                )
        else:
            response_data = {
                "message": "Current order cannot be skipped at the moment"
            }
            return Response(
                data=response_data,
                status=status.HTTP_400_BAD_REQUEST
            )

    def confirm(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        orders = Order.objects.filter(shop=self.request.user.shop)
        order = get_object_or_404(orders, **filter_kwargs)
        serializer = OrderConfirmSerializer(order, data=request.data)

        if serializer.is_valid():
            order.set_completed()
            response_data = {'message': 'Order confirmed'}
            return Response(
                data=response_data,
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                serializer.error_codes,
                status=status.HTTP_400_BAD_REQUEST
            )

    def pay(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        orders = Order.objects.filter(shop=self.request.user.shop)
        order = get_object_or_404(orders, **filter_kwargs)

        # remove previous payments for the order
        Payment.objects.filter(order=order).delete()

        # create new one
        payment = Payment.objects.create(order=order)
        success = payment.new_submit()

        order.verification_required = False
        order.save()

        if success:
            response_data = {'message': 'Paid request sent successfully'}
        else:
            response_data = {'message': 'Failed to send paid request'}

        return Response(
            data=response_data,
            status=status.HTTP_200_OK
        )


class DriverLocationViewSet(mixins.UpdateModelMixin, GenericViewSet):
    model = DriverProfile
    serializer_class = DriverLocationSerializer

    def get_object(self):
        return self.request.user.driver_profile

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        rd = request.data
        return Response(
            {'latitude': rd['latitude'], 'longitude': rd['longitude']}
        )


class DriverProfileViewSet(mixins.UpdateModelMixin,
                           mixins.RetrieveModelMixin,
                           GenericViewSet):
    model = DriverProfile
    serializer_class = DriverProfileSerializer

    def get_object(self):
        return get_object_or_404(DriverProfile, user=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if 'user' in request.data:
            user_serializer = OfintaUserSerializer(
                instance.user,
                data=request.data.pop('user'),
                partial=partial
            )
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


class ChangePasswordView(UpdateAPIView):
    """
    An endpoint for changing password.
    """
    serializer_class = ChangePasswordSerializer
    model = OfintaUser

    def get_object(self, queryset=None):
        return self.request.user

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            self.object.set_password(serializer.data.get('password'))
            self.object.changed_password = True
            self.object.save()
            return Response(
                'Password successfully changed',
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                serializer.error_codes,
                status=status.HTTP_400_BAD_REQUEST
            )


class RestorePasswordRequestView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = RestorePasswordRequestSerialzier(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = OfintaUser.objects.make_random_password(length=4,
                                                                allowed_chars='0123456789')#binascii.hexlify(os.urandom(2)).decode()
            request.session[f'{email}_restore_password_code'] = code
            body_text = f"""Enter this code: "{code}" in the application to set new password."""
            send_mail(
                subject='Your password restore code',
                message=body_text,
                from_email=settings.PASSWORD_RESTORE_EMAIL,
                recipient_list=[email]
            )
            return Response('New code generated', status=status.HTTP_200_OK)
        else:
            return Response(
                serializer.error_codes,
                status=status.HTTP_400_BAD_REQUEST
            )


class RestorePasswordSubmitView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = RestorePasswordSubmitSerialzier(
            instance=None, data=request.data, request=request
        )
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = get_object_or_404(OfintaUser, email=email)
            user.set_password(password)
            user.save()

            send_mail(
                subject='Password successfully restored',
                message=f'Your new password: {password}.',
                from_email=settings.PASSWORD_RESTORE_EMAIL,
                recipient_list=[email]
            )

            return Response(
                'Password successfully restored',
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                serializer.error_codes,
                status=status.HTTP_400_BAD_REQUEST
            )


class MessageView(mixins.CreateModelMixin,
                  mixins.ListModelMixin,
                  GenericViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def get_queryset(self):
        shop = self.request.user.shop
        return Message.objects.filter(shop=shop)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            request=self.request, data=request.data
        )
        if serializer.is_valid():
            serializer.save(
                sender=self.request.user,
                shop=self.request.user.shop
            )
            return Response(
                'Message sent',
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                serializer.error_codes,
                status=status.HTTP_400_BAD_REQUEST
            )


class UnregisterDeviceView(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        response = self.http_method_not_allowed(request, *args, **kwargs)
        return self.finalize_response(request, response, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.logout(request)

    def logout(self, request):
        device_id = request.data.get('device_id')
        if device_id:
            GCMDevice.objects.filter(
                user=request.user,
                device_id=device_id
            ).delete()

        return Response(
            {"detail": "Successfully logged out."},
            status=status.HTTP_200_OK
        )
