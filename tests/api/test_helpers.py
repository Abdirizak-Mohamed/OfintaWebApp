# third party
import pytest
from rest_framework import serializers

# ofinta
from apps.api.helpers import CustomValidationSerializer


class CharFieldsSerializer(serializers.Serializer, CustomValidationSerializer):
    domain = 'test'
    error_codes = []

    charfield_1 = serializers.CharField(allow_blank=True)
    charfield_2 = serializers.CharField(allow_null=True)
    charfield_3 = serializers.CharField(min_length=5, max_length=10)
    charfield_4 = serializers.CharField(min_length=5, max_length=10)

    def to_internal_value(self, data):
        for field in self.fields:
            self.run_custom_validation(field, data)

        validated_data = super(CharFieldsSerializer, self).to_internal_value(data)
        return validated_data


class EmailFieldsSerializer(serializers.Serializer, CustomValidationSerializer):
    domain = 'test'
    error_codes = []

    emailfield_1 = serializers.EmailField(allow_blank=True)
    emailfield_2 = serializers.EmailField(allow_null=True)
    emailfield_3 = serializers.EmailField(min_length=8, max_length=10)
    emailfield_4 = serializers.EmailField(min_length=8, max_length=10)
    emailfield_5 = serializers.EmailField(min_length=8, max_length=10)

    def to_internal_value(self, data):
        for field in self.fields:
            self.run_custom_validation(field, data)

        validated_data = super(EmailFieldsSerializer, self).to_internal_value(data)
        return validated_data


class DecimalFieldsSerializer(serializers.Serializer, CustomValidationSerializer):
    domain = 'test'
    error_codes = []

    decimalfield_1 = serializers.DecimalField(max_digits=5, decimal_places=2)
    decimalfield_2 = serializers.DecimalField(max_digits=6, decimal_places=3)

    def to_internal_value(self, data):
        for field in self.fields:
            self.run_custom_validation(field, data)

        validated_data = super(DecimalFieldsSerializer, self).to_internal_value(data)
        return validated_data


class FloatFieldsSerializer(serializers.Serializer, CustomValidationSerializer):
    domain = 'test'
    error_codes = []

    floatfield_1 = serializers.FloatField(min_value=3, max_value=5)
    floatfield_2 = serializers.FloatField(min_value=3, max_value=5)
    floatfield_3 = serializers.FloatField(min_value=1, max_value=4)

    def to_internal_value(self, data):
        for field in self.fields:
            self.run_custom_validation(field, data)

        validated_data = super(FloatFieldsSerializer, self).to_internal_value(data)
        return validated_data


class TestCustomErrorCodes:
    pytestmark = pytest.mark.django_db

    def test_charfield_error_codes(self, client):
        """
        Test serializer return proper custom codes
        """
        charfield_1 = None
        charfield_2 = ''
        charfield_3 = 'tst'
        charfield_4 = '123456789012'
        data = {
            'charfield_1': charfield_1,
            'charfield_2': charfield_2,
            'charfield_3': charfield_3,
            'charfield_4': charfield_4
        }
        cfs = CharFieldsSerializer(data=data)
        assert cfs.is_valid() is False
        assert cfs.error_codes == [
            {
                'domain': 'test.error',
                'code': 201,
                'desc': 'charfield_1 is invalid'
            },
            {
                'domain': 'test.error',
                'code': 202,
                'desc': 'charfield_2 is a required field'
            },
            {
                'domain': 'test.error',
                'code': 203,
                'desc': 'charfield_3 length is less than min length value (5)'
            },
            {
                'domain': 'test.error',
                'code': 204,
                'desc': 'charfield_4 length exceeds max length value (10)'
            }
        ]
        pass

    def test_emailield_error_codes(self, client):
        """
        Test serializer return proper custom codes
        """
        emailfield_1 = None
        emailfield_2 = ''
        emailfield_3 = 'e@e.com'
        emailfield_4 = 'email@example.com'
        emailfield_5 = 'wrongemail'
        data = {
            'emailfield_1': emailfield_1,
            'emailfield_2': emailfield_2,
            'emailfield_3': emailfield_3,
            'emailfield_4': emailfield_4,
            'emailfield_5': emailfield_5
        }
        efs = EmailFieldsSerializer(data=data)
        assert efs.is_valid() is False
        assert efs.error_codes == [
            {
                'domain': 'test.error',
                'code': 201,
                'desc': 'emailfield_1 is invalid'
            },
            {
                'domain': 'test.error',
                'code': 202,
                'desc': 'emailfield_2 is a required field'
            },
            {
                'domain': 'test.error',
                'code': 203,
                'desc': 'emailfield_3 length is less than min length value (8)'
            },
            {
                'domain': 'test.error',
                'code': 204,
                'desc': 'emailfield_4 length exceeds max length value (10)'
            },
            {
                'domain': 'test.error',
                'code': 201,
                'desc': 'emailfield_5 is invalid'
            }
        ]

    def test_decimalfield_error_codes(self, client):
        """
        Test serializer return proper custom codes
        """
        floatfield_1 = 'erdqew'
        floatfield_2 = 2.1
        floatfield_3 = 6.8
        data = {
            'floatfield_1': floatfield_1,
            'floatfield_2': floatfield_2,
            'floatfield_3': floatfield_3
        }
        ffs = FloatFieldsSerializer(data=data)
        assert ffs.is_valid() is False
        assert ffs.error_codes == [
            {
                'domain': 'test.error',
                'code': 201,
                'desc': 'floatfield_1 is invalid'
            },
            {
                'domain': 'test.error',
                'code': 205,
                'desc':  'floatfield_2 value is less than min value (3)'
            },
            {
                'domain': 'test.error',
                'code': 206,
                'desc':  'floatfield_3 value exceeds max value (4)'
            }
        ]

