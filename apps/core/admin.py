# django
from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.sessions.models import Session

# ofinta
from apps.core.models import Request
from .models import OfintaUser


class RequestAdmin(ModelAdmin):
    list_display = (
        'id', 'response', 'method', 'path', 'time', 'is_secure', 'is_ajax',
        'ip', 'user', 'referer', 'user_agent'
    )
    search_fields = ('path', 'ip', 'referer')


admin.site.register(Request, RequestAdmin)


@admin.register(OfintaUser)
class OfintaUserAdmin(DjangoUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Role'), {'fields': ('role', )}),
        (None, {'fields': ('shop', )}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (None, {'fields': ('changed_password', )}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = (
        'email', 'first_name', 'last_name', 'is_staff', 'is_active',
        'changed_password'
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email', )


class SessionAdmin(ModelAdmin):

    def _session_data(self, obj):
        return obj.get_decoded()

    list_display = ['session_key', '_session_data', 'expire_date']


admin.site.register(Session, SessionAdmin)
