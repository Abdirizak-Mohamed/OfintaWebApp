# Generated by Django 2.0.3 on 2018-08-01 13:23

import apps.core.managers
import apps.core.mixins
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('shops', '0001_initial'),
        ('auth', '0009_alter_user_last_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='OfintaUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('role', models.PositiveSmallIntegerField(choices=[(1, 'owner'), (2, 'manager'), (3, 'administrator'), (4, 'driver')], default=3, verbose_name='type')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='email address')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('shop', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='users', to='shops.Shop', verbose_name='shop')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            bases=(models.Model, apps.core.mixins.ModelDiffMixin),
            managers=[
                ('objects', apps.core.managers.OfintaUserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Request',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('response', models.SmallIntegerField(choices=[(100, 'Continue'), (101, 'Switching Protocols'), (102, 'Processing (WebDAV)'), (200, 'OK'), (201, 'Created'), (202, 'Accepted'), (203, 'Non-Authoritative Information'), (204, 'No Content'), (205, 'Reset Content'), (206, 'Partial Content'), (207, 'Multi-Status (WebDAV)'), (300, 'Multiple Choices'), (301, 'Moved Permanently'), (302, 'Found'), (303, 'See Other'), (304, 'Not Modified'), (305, 'Use Proxy'), (306, 'Switch Proxy'), (307, 'Temporary Redirect'), (400, 'Bad Request'), (401, 'Unauthorized'), (402, 'Payment Required'), (403, 'Forbidden'), (404, 'Not Found'), (405, 'Method Not Allowed'), (406, 'Not Acceptable'), (407, 'Proxy Authentication Required'), (408, 'Request Timeout'), (409, 'Conflict'), (410, 'Gone'), (411, 'Length Required'), (412, 'Precondition Failed'), (413, 'Request Entity Too Large'), (414, 'Request-URI Too Long'), (415, 'Unsupported Media Type'), (416, 'Requested Range Not Satisfiable'), (417, 'Expectation Failed'), (418, "I'm a teapot"), (422, 'Unprocessable Entity (WebDAV)'), (423, 'Locked (WebDAV)'), (424, 'Failed Dependency (WebDAV)'), (425, 'Unordered Collection'), (426, 'Upgrade Required'), (449, 'Retry With'), (500, 'Internal Server Error'), (501, 'Not Implemented'), (502, 'Bad Gateway'), (503, 'Service Unavailable'), (504, 'Gateway Timeout'), (505, 'HTTP Version Not Supported'), (506, 'Variant Also Negotiates'), (507, 'Insufficient Storage (WebDAV)'), (509, 'Bandwidth Limit Exceeded'), (510, 'Not Extended')], default=200, verbose_name='Response')),
                ('method', models.CharField(default='GET', max_length=7, verbose_name='method')),
                ('path', models.CharField(max_length=255, verbose_name='path')),
                ('time', models.DateTimeField(auto_now_add=True, verbose_name='time')),
                ('is_secure', models.BooleanField(default=False, verbose_name='is secure')),
                ('is_ajax', models.BooleanField(default=False, help_text='Whether this request was used via javascript.', verbose_name='is ajax')),
                ('data', models.TextField(blank=True, null=True)),
                ('response_content', models.TextField(blank=True, null=True)),
                ('ip', models.GenericIPAddressField(verbose_name='ip address')),
                ('referer', models.URLField(blank=True, max_length=255, null=True, verbose_name='referer')),
                ('user_agent', models.CharField(blank=True, max_length=255, null=True, verbose_name='User agent')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'verbose_name': 'request',
                'verbose_name_plural': 'requests',
                'ordering': ('-time',),
            },
        ),
    ]
