# django
from django.contrib.gis.geos import Point
from django.core.exceptions import PermissionDenied

# third party
from drf_dynamic_fields import DynamicFieldsMixin
from drf_extra_fields.fields import Base64ImageField
from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework_gis.serializers import GeoFeatureModelSerializer

# ofinta
from apps.api.helpers import CustomValidationSerializer
from apps.core.models import UserRoles, OfintaUser
from apps.core.utils import get_coordinates_by_address
from apps.management.chat.models import Message
from apps.management.drivers.models import DriverProfile
from apps.management.orders.constants import OrderStatus, PaymentMethod
from apps.management.orders.models import Order, Position, Payment
from apps.management.warehouses.models import Warehouse
from apps.shared.models import Location
from apps.api import constants


class OrderPositionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Position
        fields = ('name', 'quantity', 'price', 'item_id')


class OfintaUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = OfintaUser
        fields = ('email', 'first_name', 'last_name')


class LocationSerializer(GeoFeatureModelSerializer,
                         CustomValidationSerializer):
    domain = 'location'
    error_codes = []

    class Meta:
        model = Location
        fields = ('address', 'coordinates', )
        required_fields = ('address', )
        geo_field = 'coordinates'

    def create(self, validated_data):
        address = validated_data['address']
        lat, lng = get_coordinates_by_address(address)

        location = Location.objects.create(
            address=address,
            coordinates=Point(lat, lng)
        )
        return location

    def to_internal_value(self, data):
        for field in self.fields:
            self.run_custom_validation(field, data)

        validated_data = super(LocationSerializer, self).to_internal_value(data)
        return validated_data


class WarehouseSerializer(serializers.ModelSerializer):
    location = LocationSerializer()

    class Meta:
        model = Warehouse
        fields = ('code', 'name', 'location')
        read_only_fields = ('name', 'location', )


class OrderSerializer(DynamicFieldsMixin,
                      WritableNestedModelSerializer,
                      CustomValidationSerializer):
    domain = 'order'
    error_codes = []

    positions = OrderPositionSerializer(many=True)
    shipping_address = LocationSerializer()
    warehouse = serializers.SlugRelatedField(
        slug_field='code', queryset=Warehouse.objects.all()
    )
    warehouse_location = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    status_verbose = serializers.SerializerMethodField()

    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            'shipping_address', 'delivery_fee', 'buyer_name', 'buyer_phone',
            'buyer_email', 'payment_method', 'positions', 'warehouse',
            'order_number', 'is_active', 'status', 'warehouse_location',
            'id', 'status_verbose', 'is_paid', 'pending_transaction',
            'verification_required', 'is_payment_link', 'total_amount'
        )
        read_only_fields = ('id', 'warehouse_location', 'is_paid')
        required_fields = (
            'buyer_name', 'buyer_phone', 'order_number',
            'shipping_address.address'
        )
        extra_kwargs = {
            'status': {'write_only': True},
        }

    def to_internal_value(self, data):
        for field in self.fields:
            self.run_custom_validation(field, data)

        validated_data = super(OrderSerializer, self).to_internal_value(data)
        return validated_data

    def get_is_active(self, order):
        return order.status not in [
            OrderStatus.CANCELED, OrderStatus.COMPLETED
        ]

    def get_total_amount(self, order):
        return str(order.total_price())

    def get_status_verbose(self, order):
        return order.status_verbose

    def get_warehouse_location(self, order):
        serializer = WarehouseSerializer(order.warehouse)
        return serializer.data

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        shop = user.shop
        if not shop:
            raise PermissionDenied()

        validated_data.update(**{'shop': shop})
        order = super().create(validated_data)

        if order.payment_method == PaymentMethod.MPESA:
            payment = Payment.objects.create(order=order)
            payment.new_submit()

        return order


class OrderConfirmSerializer(DynamicFieldsMixin,
                             WritableNestedModelSerializer,
                             CustomValidationSerializer):
    domain = 'order'
    error_codes = []

    class Meta:
        model = Order
        fields = ('verification_code', )
        required_fields = ('verification_code', )

    def to_internal_value(self, data):
        for field in self.fields:
            self.run_custom_validation(field, data)

        validated_data = super(
            OrderConfirmSerializer, self
        ).to_internal_value(data)
        return validated_data

    def validate(self, data):
        code = data.get('verification_code', '')

        # validate code only if order is paid via MPesa
        if self.instance.payment_method == PaymentMethod.MPESA:
            order_exists = Order.objects.filter(verification_code=code).exists()
            if not order_exists or not code:
                self.error_codes.append(
                    {
                        'domain': self.domain + '.error',
                        'code': constants.WRONG_VERIFICATION_CODE,
                        'desc': f'Incorrect verification code'
                    }
                )
                raise serializers.ValidationError(f'Provided code is invalid')

        return code


class DriverAuthTokenSerializer(AuthTokenSerializer):

    def validate(self, attrs):
        attr = super().validate(attrs)
        user = attr['user']
        if not user.role == UserRoles.DRIVER:
            raise serializers.ValidationError(
                'Only drivers can obtain API token',
                code='authorization'
            )

        return attrs


class DriverLocationSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)

    class Meta:
        model = DriverProfile
        fields = ('latitude', 'longitude')

    def update(self, instance, validated_data):
        latitude = validated_data.pop('latitude')
        longitude = validated_data.pop('longitude')
        instance = super().update(instance, validated_data)
        coordinates = Point(latitude, longitude)
        instance.coordinates = coordinates
        instance.save()
        return instance


class DriverProfileSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.user.changed_password:
            del self.fields['changed_password']

    user = OfintaUserSerializer()
    photo = Base64ImageField(allow_null=True)
    changed_password = serializers.SerializerMethodField()

    class Meta:
        model = DriverProfile
        read_only_fields = ('coordinates', )
        exclude = ('id', )

    def get_changed_password(self, obj):
        return obj.user.changed_password


class ChangePasswordSerializer(serializers.Serializer,
                               CustomValidationSerializer):
    error_codes = []
    domain = 'change_password'

    password = serializers.CharField(required=True)

    def to_internal_value(self, data):
        for field in self.fields:
            self.run_custom_validation(field, data)

        validated_data = super(
            ChangePasswordSerializer, self
        ).to_internal_value(data)
        return validated_data


class RestorePasswordRequestSerialzier(serializers.Serializer,
                                       CustomValidationSerializer):
    error_codes = []
    domain = 'restore_password'

    email = serializers.EmailField(required=True)

    def to_internal_value(self, data):
        for field in self.fields:
            self.run_custom_validation(field, data)

        email = data['email']
        if not OfintaUser.objects.filter(email=email).exists():
            self.error_codes.append(
                {
                    'domain': self.domain + '.error',
                    'code': constants.NO_USER,
                    'desc': f'User with email {email} does not exists'
                }
            )

        validated_data = super(
            RestorePasswordRequestSerialzier, self
        ).to_internal_value(data)
        return validated_data

    def validate_email(self, email):
        if not OfintaUser.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                'User with email "{}" does not exists'.format(email)
            )

        return email


class RestorePasswordSubmitSerialzier(serializers.Serializer,
                                      CustomValidationSerializer):
    error_codes = []
    domain = 'restore_password'

    code = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)

    def __init__(self, instance, data, request, *args, **kwargs):
        self.request = request
        super().__init__(instance, data, *args, **kwargs)

    def to_internal_value(self, data):
        for field in self.fields:
            self.run_custom_validation(field, data)

        email = data['email']
        if not OfintaUser.objects.filter(email=email).exists():
            self.error_codes.append(
                {
                    'domain': self.domain + '.error',
                    'code': constants.NO_USER,
                    'desc': f'User with email "{email}" does not exists'
                }
            )

        code = data['code']
        code_from_session = self.request.session.get(
            f'{email}_restore_password_code'
        )

        if code != code_from_session:
            self.error_codes.append(
                {
                    'domain': self.domain + '.error',
                    'code': constants.CODES_NOT_MATCH,
                    'desc': f'Codes does not match'
                }
            )

        validated_data = super(
            RestorePasswordSubmitSerialzier, self
        ).to_internal_value(data)
        return validated_data

    def validate_email(self, email):
        if not OfintaUser.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                f'User with email "{email}" does not exists'
            )

        return email

    def validate(self, attrs):
        email = attrs['email']
        code = attrs['code']
        session_key = f'{email}_restore_password_code'
        code_from_session = self.request.session.get(session_key)
        if code != code_from_session:
            raise serializers.ValidationError('Codes does not match')

        return attrs


class MessageSerializer(serializers.ModelSerializer,
                        CustomValidationSerializer):
    domain = 'chat'
    error_codes = []

    sender = serializers.SlugRelatedField(
        many=False,
        slug_field='email',
        queryset=OfintaUser.objects.all(),
        required=False
    )

    class Meta:
        model = Message
        fields = ('sender', 'message', 'timestamp')
        read_only_fields = ('sender', 'timestamp')

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request:
            user = request.user

            self.fields['sender'].queryset = OfintaUser.objects.filter(
                role__in=[UserRoles.DRIVER, UserRoles.MANAGER, UserRoles.OWNER],
                shop=user.shop
            )

    def to_internal_value(self, data):
        for field in self.fields:
            self.run_custom_validation(field, data)

        validated_data = super(MessageSerializer, self).to_internal_value(data)
        return validated_data
