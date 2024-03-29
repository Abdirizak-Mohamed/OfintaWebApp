# django
from django.contrib import admin

# ofinta
from apps.management.orders.models import Order, Position, OrderAssignments, \
    Payment


class PositionAdmin(admin.TabularInline):
    """
    Order model admin
    """
    model = Position
    list_display = (
        'item_id',
        'name',
        'quantity',
        'price'
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Order model admin
    """
    inlines = [PositionAdmin, ]
    list_display = (
        'order_number',
        'buyer_name',
        'buyer_phone',
        'buyer_email',
        'status',
        'shop',
        'driver',
        'created_at',
        'completed_at',
        'payment_method'
    )


admin.site.register(Payment)
admin.site.register(OrderAssignments)
