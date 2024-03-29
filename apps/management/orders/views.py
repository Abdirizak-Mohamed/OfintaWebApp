# django
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms.utils import ErrorList
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView, UpdateView, CreateView

# ofinta
from apps.management.orders.constants import OrderStatus
from apps.management.orders.forms import OrderEditForm, OrderCancelForm, \
    OrderSearchForm, DriverAssignForm, OrderShippingAddressForm, \
    OrderPositionFormSet, PaymentLinkEditForm, PaymentLinkCreateForm, \
    PaymentLinkCancelForm
from apps.management.orders.mixins import OrdersMixin, PaymentLinksMixin
from apps.management.orders.models import Order, OrderAssignments
from apps.management.pricelist.forms import PriceListSearchForm
from apps.management.pricelist.models import PriceListItem

from apps.management.mixins import ManagerTestMixin

from apps.mpesa_gateway.models import TransactionStatus


class OrdersList(ManagerTestMixin, OrdersMixin, ListView):
    model = Order
    template_name = 'management/orders/orders_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        user = self.request.user
        shop = user.shop
        return shop.get_orders().get_open()

    def filter_queryset(self, queryset):
        search_form = OrderSearchForm(self.request.GET)
        if search_form.is_valid():
            cd = search_form.cleaned_data
            order_number = cd['order_number']
            start_date = cd['start_date']
            end_date = cd['end_date']
            if start_date:
                queryset = queryset.filter(created_at__gte=start_date)

            if end_date:
                queryset = queryset.filter(created_at__lte=end_date)

            if order_number:
                queryset = queryset.filter(order_number__contains=order_number)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        orders = context['orders']
        orders = self.filter_queryset(orders)

        orders_coords = []
        for order in orders:
            shipping_address = order.shipping_address
            if not shipping_address.coordinates:
                continue

            latitude = shipping_address.coordinates.x
            longtitude = shipping_address.coordinates.y

            orders_coords.append([latitude, longtitude])
            orders_coords.append([latitude, longtitude])

        context['orders'] = orders

        form = OrderSearchForm(self.request.GET or None)
        form.is_valid()
        context['search_form'] = form
        context['orders_coords'] = orders_coords
        return context


class OrdersHistory(ManagerTestMixin, OrdersMixin, ListView):
    model = Order
    template_name = 'management/orders/orders_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        user = self.request.user
        shop = user.shop
        return shop.get_orders().get_recent()


class OrderDetails(ManagerTestMixin, OrdersMixin, DetailView):
    model = Order
    template_name = 'management/orders/order_details.html'
    context_object_name = 'order'

    def get_context_data(self, **kwargs):
        order = self.get_object()
        context = super().get_context_data()
        context['form'] = OrderCancelForm(instance=order)
        return context


class PaymentLinksList(ManagerTestMixin, PaymentLinksMixin, ListView):
    model = Order
    template_name = 'management/orders/payment_links_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        user = self.request.user
        shop = user.shop
        return shop.get_orders().get_pl()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        ctx['form'] = PaymentLinkCancelForm()
        return ctx


class PaymentLinkEdit(UpdateView):
    model = Order
    template_name = 'management/orders/payment_link_edit.html'
    context_object_name = 'order'
    form_class = PaymentLinkEditForm
    slug_field = 'payment_link_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        order = self.get_object()

        txn = order.get_transaction()
        if txn:
            if txn.status == TransactionStatus.CANCEL:
                context['txn_warning'] = 'Canceled by phone user'

        payment_link_form = PaymentLinkEditForm(instance=order)
        payment_link_form.fields['buyer_phone'].required = True
        payment_link_form.fields['payment_method'].choices = filter(
            lambda x: x[0] != '',
            payment_link_form.fields['payment_method'].choices
        )
        context['form'] = payment_link_form

        shipping_address_form = OrderShippingAddressForm(
            instance=order.shipping_address
        )
        shipping_address_form.fields['address'].required = True

        context['shipping_address_form'] = shipping_address_form
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        order_form = self.get_form()
        shipping_address_form = OrderShippingAddressForm(
            data=self.request.POST,
            instance=self.get_object().shipping_address
        )

        if all((order_form.is_valid(), shipping_address_form.is_valid())):
            order = order_form.save(commit=False)
            shipping_address = shipping_address_form.save()
            order.shipping_address = shipping_address
            order.save()
            pay = bool(order_form.cleaned_data.get('pay'))
            request.session['pay'] = pay
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(order_form)

    def get_success_url(self):
        return reverse(
            'payment-link-success',
            args=(self.get_object().payment_link_id, )
        )


class PaymentLinkDetails(ManagerTestMixin, PaymentLinksMixin, DetailView):
    model = Order
    template_name = 'management/orders/order_details.html'
    context_object_name = 'order'
    slug_field = 'payment_link_id'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        ctx['form'] = PaymentLinkCancelForm()
        return ctx

    def get(self, request, *args, **kwargs):
        # if not payment link was found - redirect to corresponding order
        qset = self.get_queryset()
        slug = self.kwargs.get(self.slug_url_kwarg)
        pl_exists = qset.filter(payment_link_id=slug).exists()
        if not pl_exists:
            pl = self.get_object(Order.objects.all())
            return redirect(
                reverse('management:order-details', args=(pl.id,))
            )

        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class PaymentLinkCancel(ManagerTestMixin, PaymentLinksMixin, UpdateView):
    model = Order
    template_name = 'management/orders/order_details.html'
    context_object_name = 'order'
    slug_field = 'payment_link_id'
    form_class = PaymentLinkCancelForm

    def get_success_url(self):
        return reverse('orders-list')


class PaymentLinkStep1(DetailView):
    template_name = 'management/orders/payment_link_step_1.html'
    model = Order
    context_object_name = 'order'
    slug_field = 'payment_link_id'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        order = ctx['order']

        pay = self.request.session['pay']
        able_to_pay = pay and order.shop.allow_prepayment
        ctx['pay'] = able_to_pay
        return ctx


class PaymentLinkStep2(DetailView):
    template_name = 'management/orders/payment_link_step_2.html'
    model = Order
    context_object_name = 'order'
    slug_field = 'payment_link_id'


class OrderEdit(ManagerTestMixin, OrdersMixin, UpdateView):
    model = Order
    form_class = OrderEditForm
    template_name = 'management/orders/order_edit.html'
    context_object_name = 'order'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        order_form = self.get_form()
        shipping_address_form = OrderShippingAddressForm(
            data=self.request.POST,
            instance=self.get_object().shipping_address
        )

        if all((order_form.is_valid(), shipping_address_form.is_valid())):
            order = order_form.save(commit=False)
            shipping_address = shipping_address_form.save()
            order.shipping_address = shipping_address
            order.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(order_form)

    def get_success_url(self):
        order = self.get_object()
        return reverse('management:order-details', args=(order.pk, ))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['shipping_address_form'] = OrderShippingAddressForm(
            instance=self.get_object().shipping_address
        )
        return context


class PaymentLinkCreate(ManagerTestMixin, CreateView):
    model = Order
    form_class = PaymentLinkCreateForm
    template_name = 'management/orders/order_create.html'
    context_object_name = 'order'
    object = None

    def get(self, request, *args, **kwargs):
        shop = request.user.shop
        if not shop.filled:
            messages.add_message(
                request, messages.INFO,
                'You should set up your shop first'
            )
            return redirect(reverse('management:edit-shop'))
        return super().get(request, args, kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def post(self, request, *args, **kwargs):
        add_missing_products = self.request.POST.get('add_missing_products')
        order_form = self.get_form()
        shipping_address_form = OrderShippingAddressForm(
            data=self.request.POST
        )

        if all((order_form.is_valid(), shipping_address_form.is_valid())):
            self.object = order_form.save(commit=False)
            shipping_address = shipping_address_form.save()
            self.object.shop = request.user.shop
            self.object.shipping_address = shipping_address

            context = self.get_context_data()
            order_formset = context['order_formset']
            if order_formset.is_valid():
                self.object.save()
                positions = order_formset.save(commit=False)
                for p in positions:
                    p.order = self.object
                    p.save()

                    if add_missing_products and not \
                        PriceListItem.objects.filter(
                            item_id=p.item_id
                        ).exists():
                        PriceListItem.objects.create(
                            item_id=p.item_id,
                            name=p.name,
                            price=p.price,
                            currency=p.currency,
                            shop=p.order.shop

                        )
            else:
                return self.render_to_response(context)

            return HttpResponseRedirect(self.get_success_url())
        
        else:
            return self.render_to_response(self.get_context_data())

    def get_success_url(self):
        return reverse('management:order-details', args=(self.object.id, ))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shop = self.request.user.shop
        pricelist_items = shop.get_pricelist_items()

        context['pricelist_items'] = pricelist_items
        context['pricelist_search_form'] = PriceListSearchForm(
            **{'user': self.request.user}
        )

        if self.request.POST:
            context['shipping_address_form'] = OrderShippingAddressForm(
                self.request.POST
            )
            context['order_formset'] = OrderPositionFormSet(self.request.POST)
        else:
            context['shipping_address_form'] = OrderShippingAddressForm()
            context['order_formset'] = OrderPositionFormSet()
        return context


class OrderCancel(ManagerTestMixin, OrdersMixin, UpdateView):
    model = Order
    form_class = OrderCancelForm
    template_name = 'management/orders/order_details.html'
    context_object_name = 'order'

    def get_success_url(self):
        order = self.get_object()
        return reverse('management:order-details', args=(order.pk, ))


class DriverAssign(ManagerTestMixin, CreateView):
    model = OrderAssignments
    form_class = DriverAssignForm
    template_name = 'management/orders/driver_assign.html'

    def _get_order(self):
        shop = self.request.user.shop
        order = get_object_or_404(shop.orders.all(), pk=self.kwargs['pk'])
        return order

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = self._get_order()
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['order'] = self._get_order()
        return kwargs

    def get_success_url(self):
        order = self._get_order()
        return reverse(
            'management:order-details', args=(order.pk, )
        )
