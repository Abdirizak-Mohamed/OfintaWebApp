# system
import decimal

# django
from django.core.validators import EmailValidator, validate_ipv46_address, \
    RegexValidator

# third party
# from django.utils.encoding import smart_text
from django.utils.formats import sanitize_separators
from rest_framework.exceptions import ValidationError

# ofinta
from apps.api import constants


class CustomValidationSerializer:

    def generate_required_code(self, field):
        return {
            'domain': self.domain + '.error',
            'code': constants.REQUIRED_FIELD,
            'desc': f'{field.field_name} is a required field'
        }

    def generate_invalid_code(self, field, description=None):
        return {
            'domain': self.domain + '.error',
            'code': constants.INVALID_VALUE,
            'desc': description or f'{field.field_name} is invalid'
        }

    def generate_min_length_code(self, field):
        return {
            'domain': self.domain + '.error',
            'code': constants.MIN_LENGTH,
            'desc': f'{field.field_name} length is less than min length value '
                    f'({field.min_length})'
        }

    def generate_max_length_code(self, field):
        return {
            'domain': self.domain + '.error',
            'code': constants.MAX_LENGTH,
            'desc': f'{field.field_name} length exceeds max length value '
                    f'({field.max_length})'
        }

    def generate_min_value_code(self, field):
        return {
            'domain': self.domain + '.error',
            'code': constants.MIN_VALUE,
            'desc': f'{field.field_name} value is less than min value '
                    f'({field.min_value})'
        }

    def generate_max_value_code(self, field):
        return {
            'domain': self.domain + '.error',
            'code': constants.MAX_VALUE,
            'desc': f'{field.field_name} value exceeds max value '
                    f'({field.max_value})'
        }

    def validate_charfield(self, field, data):
        if data == '' or (
                field.trim_whitespace and str(data).strip() == ''
        ):
            if not field.allow_blank:
                self.error_codes.append(self.generate_required_code(field))
                return data, False
            else:
                return '', True

        elif isinstance(data, bool) or not isinstance(data, (str, int, float)):
            self.error_codes.append(self.generate_invalid_code(field))
            return data, False

        self.validate_length(field, data)
        return data, True

    def validate_length(self, field, data):
        if field.max_length is not None:
            if len(data) > field.max_length:
                self.error_codes.append(self.generate_max_length_code(field))
        if field.min_length is not None:
            if len(data) < field.min_length:
                self.error_codes.append(self.generate_min_length_code(field))

    def validate_decimalfield(self, field, data):
        data = str(data).strip()
        if field.localize:
            data = sanitize_separators(data)

        if len(data) > field.MAX_STRING_LENGTH:
            self.error_codes.append(self.generate_max_length_code(field))
            return data

        try:
            value = decimal.Decimal(data)
        except decimal.DecimalException as e:
            self.error_codes.append(self.generate_invalid_code(field))
            return data

        # Check for NaN. It is the only value that isn't equal to itself,
        # so we can use this to identify NaN values.
        if value != value:
            self.error_codes.append(self.generate_invalid_code(field))
            return data

        # Check for infinity and negative infinity.
        if value in (decimal.Decimal('Inf'), decimal.Decimal('-Inf')):
            self.error_codes.append(self.generate_invalid_code(field))
            return data

        sign, digittuple, exponent = value.as_tuple()

        if exponent >= 0:
            # 1234500.0
            total_digits = len(digittuple) + exponent
            whole_digits = total_digits
            decimal_places = 0
        elif len(digittuple) > abs(exponent):
            # 123.45
            total_digits = len(digittuple)
            whole_digits = total_digits - abs(exponent)
            decimal_places = abs(exponent)
        else:
            # 0.001234
            total_digits = abs(exponent)
            whole_digits = 0
            decimal_places = total_digits

        if field.max_digits is not None and \
                total_digits > field.max_digits:
            description = (f'{field.field_name} exceeds max digits '
                           f'({field.max_digits}) value')
            self.error_codes.append(
                self.generate_invalid_code(field, description)
            )
            return data
        if field.decimal_places is not None and \
                decimal_places > field.decimal_places:
            description = (f'{field.field_name} exceeds max decimal '
                           f'places ({field.decimal_places}) value')
            self.error_codes.append(
                self.generate_invalid_code(field, description)
            )
            return data
        if field.max_whole_digits is not None and whole_digits > field.max_whole_digits:
            description = (f'{field.field_name} exceeds max while digits '
                           f'({field.max_whole_digits}) value')
            self.error_codes.append(
                self.generate_invalid_code(field, description)
            )
            return data
        return value

    def _validate_email_domain_part(self, domain_part):
        if EmailValidator.domain_regex.match(domain_part):
            return True

        literal_match = EmailValidator.literal_regex.match(domain_part)
        if literal_match:
            ip_address = literal_match.group(1)
            try:
                validate_ipv46_address(ip_address)
                return True
            except ValidationError:
                pass

        return False

    def validate_emailfield(self, field, data):
        data, valid = self.validate_charfield(field, data)
        if not valid:
            return data

        if not data or '@' not in data:
            self.error_codes.append(self.generate_invalid_code(field))
            return data

        user_part, domain_part = data.rsplit('@', 1)
        if not EmailValidator.user_regex.match(user_part):
            self.error_codes.append(self.generate_invalid_code(field))
            return data

        if not self._validate_email_domain_part(domain_part):
            # Try for possible IDN domain-part
            try:
                domain_part = domain_part.encode('idna').decode('ascii')
            except UnicodeError:
                pass
            else:
                if not self._validate_email_domain_part(domain_part):
                    self.error_codes.append(self.generate_invalid_code(field))
                    return data
        return data

    def validate_regexfield(self, field, data):
        data = self.validate_charfield(field, data)
        regex_matches = bool(RegexValidator.regex.search(str(data)))
        invalid_input = regex_matches if RegexValidator.inverse_match \
            else not regex_matches
        if invalid_input:
            self.error_codes.append(self.generate_invalid_code(field))

        return data

    def validate_floatfield(self, field, data):
        try:
            float(data)
        except (TypeError, ValueError):
            self.error_codes.append(self.generate_invalid_code(field))
            return data

        if data < field.min_value:
            self.error_codes.append(self.generate_min_value_code(field))
            return data

        if data > field.max_value:
            self.error_codes.append(self.generate_max_value_code(field))
            return data
        return data

    def run_custom_validation(self, field, data):
        field_value = data.get(field, None)
        field_instance = self.fields.get(field)
        field_class = field_instance.__class__.__name__
        if field_class == 'CharField':
            self.validate_charfield(field_instance, field_value)
        elif field_class == 'DecimalField':
            self.validate_decimalfield(field_instance, field_value)
        elif field_class == 'EmailField':
            self.validate_emailfield(field_instance, field_value)
        elif field_class == 'FloatField':
            self.validate_floatfield(field_instance, field_value)
