# system
import re

# django
from _socket import gethostbyaddr

from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

# ofinta
from apps.core.managers import OfintaUserManager
from apps.core.mixins import ModelDiffMixin
from apps.core.utils import browsers, engines, HTTP_STATUS_CODES, chunked_to_max
from apps.management.shops.models import Shop


class UserRoles:
    OWNER = 1
    MANAGER = 2
    ADMINISTRATOR = 3
    DRIVER = 4
    CHOICES = (
        (OWNER, 'owner'),
        (MANAGER, 'manager'),
        (ADMINISTRATOR, 'administrator'),
        (DRIVER, 'driver')
    )


class OfintaUser(AbstractUser, ModelDiffMixin):
    """
    Ordinary django user with role support
    """
    objects = OfintaUserManager()

    username = None
    role = models.PositiveSmallIntegerField(
        verbose_name=_('type'),
        choices=UserRoles.CHOICES,
        default=UserRoles.ADMINISTRATOR
    )
    shop = models.ForeignKey(
        Shop,
        verbose_name='shop',
        related_name='users',
        blank=True, null=True,
        on_delete=models.CASCADE
    )
    email = models.EmailField(verbose_name=_('email address'), unique=True)

    changed_password = models.BooleanField(
        verbose_name='User has changed the default password',
        default=False
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.email})'

    @property
    def is_owner(self):
        return self.role == UserRoles.OWNER

    @property
    def is_manager(self):
        return self.role == UserRoles.MANAGER

    @property
    def is_driver(self):
        return self

    @property
    def is_admin(self):
        return self.role == UserRoles.ADMINISTRATOR

    def save(self, force_insert=False, force_update=False, *args, **kwargs):

        if self.pk and 'password' in self.diff:
            self.changed_password = True

        super(OfintaUser, self).save(
            force_insert, force_update, *args, **kwargs
        )

        if self.role == UserRoles.OWNER \
                and self.diff.get('is_active') == (True, False):
            shop = self.shop
            if shop:
                managers = shop.get_managers()
                managers.update(**{'is_active': False})


class Request(models.Model):
    # Response information
    response = models.SmallIntegerField(
        'Response',
        choices=HTTP_STATUS_CODES,
        default=200
    )

    # Request information
    method = models.CharField('method', default='GET', max_length=7)
    path = models.CharField('path', max_length=255)
    time = models.DateTimeField('time', auto_now_add=True)

    is_secure = models.BooleanField('is secure', default=False)
    is_ajax = models.BooleanField(
        'is ajax',
        default=False,
        help_text='Whether this request was used via javascript.'
    )

    # POST body data
    data = models.TextField(null=True, blank=True)

    # json response content
    response_content = models.TextField(null=True, blank=True)

    # User information
    ip = models.GenericIPAddressField('ip address')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True, null=True,
        verbose_name='user',
        on_delete=models.CASCADE
    )
    referer = models.URLField('referer', max_length=255, blank=True, null=True)
    user_agent = models.CharField(
        'User agent', max_length=255,
        blank=True, null=True
    )

    class Meta:
        verbose_name = 'request'
        verbose_name_plural = 'requests'
        ordering = ('-time',)

    def __str__(self):
        return '[%s] %s %s %s' % (
            self.time, self.method, self.path, self.response
        )

    def get_user(self):
        return get_user_model().objects.get(pk=self.user.id)

    def from_http_request(self, request, response=None, commit=True):
        # Request information
        self.method = request.method
        self.path = request.path[:255]

        self.is_secure = request.is_secure()
        # self.is_ajax = request.is_ajax()

        if re.match(
                '^application/json',
                response.get('Content-Type', ''),
                re.I
        ):
            self.response_content = response.content

        # User information
        self.ip = request.META.get('REMOTE_ADDR', '')
        self.referer = request.META.get('HTTP_REFERER', '')[:255]
        self.user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
        self.language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')[:255]

        if request.method in ('POST', 'PUT'):
            # if request.body is not empty
            # if there's an image in data, it might have
            # non-utf chars and break the server on self.save() below
            # we remove those
            try:
                self.data = chunked_to_max(
                    request._body_to_log
                ).decode('utf-8', 'ignore').encode('utf-8')
            except:
                self.data = ''

        if getattr(request, 'user', False):
            if request.user.is_authenticated:
                self.user = request.user

        if response:
            self.response = response.status_code

            if (response.status_code == 301) or (response.status_code == 302):
                self.redirect = response['Location']

        if commit:
            self.save()

    @property
    def browser(self):
        if not self.user_agent:
            return

        if not hasattr(self, '_browser'):
            self._browser = browsers.resolve(self.user_agent)
        return self._browser[0]

    @property
    def keywords(self):
        if not self.referer:
            return

        if not hasattr(self, '_keywords'):
            self._keywords = engines.resolve(self.referer)
        if self._keywords:
            return ' '.join(self._keywords[1]['keywords'].split('+'))

    @property
    def hostname(self):
        try:
            return gethostbyaddr(self.ip)[0]
        except Exception:  # socket.gaierror, socket.herror, etc
            return self.ip
