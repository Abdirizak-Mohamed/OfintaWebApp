# django
from django.contrib.auth.forms import AuthenticationForm
from django import forms

from apps.core.models import UserRoles


class LoginForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        """
        Controls whether the given User may log in. This is a policy setting,
        independent of end-user authentication. This default behavior is to
        allow login by active users, and reject login by inactive users.

        If the given user cannot log in, this method should raise a
        ``forms.ValidationError``.

        If the given user may log in, this method should return None.
        """

        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )
        
        #    drivers don't login into website
        if not user.role in [UserRoles.ADMINISTRATOR, UserRoles.MANAGER, UserRoles.OWNER]:
            raise forms.ValidationError(
                "Please enter a correct email and password",
                code='invalid_login',
            )
            
