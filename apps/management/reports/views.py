# django
from django.views.generic import ListView

# ofinta
from apps.management.orders.mixins import OrdersMixin
from apps.management.orders.models import Order
from apps.management.reports.forms import ReportsFilterForm

from apps.management.mixins import ManagerTestMixin


class Reports(ManagerTestMixin, OrdersMixin, ListView):
    model = Order
    template_name = 'management/reports/reports.html'
    context_object_name = 'orders'

    def get_queryset(self):
        user = self.request.user
        shop = user.shop
        return shop.get_orders().get_open()

    def filter_queryset(self, queryset):
        search_form = ReportsFilterForm(self.request.GET)
        if search_form.is_valid():
            cd = search_form.cleaned_data
            start_date = cd['start_date']
            end_date = cd['end_date']
            if start_date:
                queryset = queryset.filter(created_at__gte=start_date)

            if end_date:
                queryset = queryset.filter(created_at__lte=end_date)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        orders = context['orders']
        orders = self.filter_queryset(orders)
        context['orders'] = orders

        form = ReportsFilterForm(self.request.GET or None)
        form.is_valid()
        context['filter_form'] = form
        return context
