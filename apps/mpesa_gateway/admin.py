from django.contrib import admin

from apps.mpesa_gateway.models import MPesaTransaction


admin.site.register(MPesaTransaction)
