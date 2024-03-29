# django
from django.urls import reverse
from django.views.generic import ListView, DetailView, UpdateView, CreateView

# ofinta
from apps.management.drivers.forms import DriverStatusForm
from apps.management.warehouses.forms import WarehouseCreateForm, \
    WarehouseEditForm
from apps.management.warehouses.mixins import WarehousesMixin
from apps.management.warehouses.models import Warehouse

from apps.management.mixins import ManagerTestMixin


class WarehousesList(ManagerTestMixin, WarehousesMixin, ListView):
    model = Warehouse
    template_name = 'management/warehouses/warehouses_list.html'
    context_object_name = 'warehouses'


class WarehouseDetails(ManagerTestMixin, WarehousesMixin, DetailView):
    model = Warehouse
    template_name = 'management/warehouses/warehouse_details.html'
    context_object_name = 'warehouse'

    def get_context_data(self, **kwargs):
        driver = self.get_object()
        context = super().get_context_data()
        context['form'] = DriverStatusForm(instance=driver)
        return context


class WarehouseAdd(ManagerTestMixin, CreateView):
    model = Warehouse
    form_class = WarehouseCreateForm
    template_name = 'management/warehouses/warehouse_add.html'

    def get_success_url(self):
        return reverse('management:warehouses-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class WarehouseEdit(ManagerTestMixin, WarehousesMixin, UpdateView):
    model = Warehouse
    form_class = WarehouseEditForm
    template_name = 'management/warehouses/warehouse_edit.html'
    context_object_name = 'warehouse'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        warehouse = self.get_object()
        return reverse('management:warehouse-details', args=(warehouse.pk, ))
