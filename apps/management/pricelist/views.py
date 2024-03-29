# django
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.forms import model_to_dict
from django.http import JsonResponse, Http404
from django.http.response import HttpResponseRedirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import CreateView
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView, DeleteView
from django.views.generic.list import ListView

# ofinta
from apps.management.mixins import ManagerTestMixin

from .forms import PriceListSearchForm, PriceListItemForm
from .mixins import PriceListMixin
from .models import PriceListItem


class PriceList(ManagerTestMixin, PriceListMixin, ListView):
    model = PriceListItem
    context_object_name = 'pricelist_items'
    template_name = 'management/pricelist/pricelist.html'

    def get(self, request, *args, **kwargs):
        if 'application/json' in request.accepts():
            pricelist_items = PriceListItem.objects.all()
            page = request.GET.get('page', 1)
            item_id = request.GET.get('item_id')
            if item_id:
                pricelist_items = pricelist_items.filter(item_id=item_id)

            item_name = request.GET.get('item_name')
            if item_name:
                pricelist_items = pricelist_items.filter(name=item_name)

            paginator = Paginator(pricelist_items, 5)
            pricelist_items_page = paginator.page(page)
            response_html = render_to_string(
                'management/orders/includes/_pricelist_items.html',
                {'pricelist_items': pricelist_items_page}
            )
            return JsonResponse({'html': response_html})

        return super().get(request, *args, **kwargs)

    def filter_queryset(self, queryset):
        search_form = PriceListSearchForm(data=self.request.GET)
        if search_form.is_valid():
            cd = search_form.cleaned_data
            item_id = cd['item_id']
            item_name = cd['name']
            if item_id:
                queryset = queryset.filter(item_id__contains=item_id)

            if item_name:
                queryset = queryset.filter(name__contains=item_name)

        return queryset

    def get_queryset(self):
        price_sort = self.request.GET.get('price_sort')
        name_sort = self.request.GET.get('name_sort')
        qset = super().get_queryset()
        if price_sort == 'asc':
            qset = qset.order_by('price')
        elif price_sort == 'desc':
            qset = qset.order_by('-price')

        if name_sort == 'asc':
            qset = qset.order_by('name')
        elif name_sort == 'desc':
            qset = qset.order_by('-name')
            
        if not name_sort and not price_sort:
            qset = qset.order_by('-item_id')
        
        return qset.filter(is_active=True)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        form = PriceListSearchForm(self.request.GET)
        form.is_valid()
        context['search_form'] = form

        pricelist_items = context['pricelist_items']
        context['pricelist_items'] = self.filter_queryset(pricelist_items)
        return context


class PriceListInactive(ManagerTestMixin, PriceListMixin, ListView):
    model = PriceListItem
    context_object_name = 'pricelist_items'
    template_name = 'management/pricelist/pricelist_inactive.html'

    def get_queryset(self):
        qset = super().get_queryset()
        return qset.filter(is_active=False)


class PriceListItemDelete(ManagerTestMixin, PriceListMixin, DeleteView):
    model = PriceListItem
    context_object_name = 'pricelist_item'
    template_name = 'management/pricelist/pricelist_item_delete.html'

    def get_queryset(self):
        qset = super().get_queryset()
        return qset.filter(is_active=True)

    def get_success_url(self):
        return reverse('management:pricelist')


class PriceListItemAdd(ManagerTestMixin, CreateView):
    models = PriceListItem
    form_class = PriceListItemForm
    queryset = PriceListItem.objects.all()

    def get_queryset(self):
        user = self.request.user
        shop = user.shop
        return shop.pricelist_items.all()

    def get(self, request, *args, **kwargs):
        user = request.user
        shop = user.shop

        pricelist_items = shop.pricelist_items.all()
        last_pricelist_item = pricelist_items.last()

        action = reverse('management:pricelist-item-add')
        if last_pricelist_item:
            
            try:
                item_id_int = int(last_pricelist_item.item_id)
                
            except:
                item_id_int = None
            
            if item_id_int:
                item_id = '{0:0>4}'.format(
                    str(item_id_int + 1)
                )
            
            else:
                item_id = ""
                
            form = PriceListItemForm(initial={'item_id': item_id})
        else:
            form = PriceListItemForm()

        html = render_to_string(
            'management/pricelist/includes/_pricelist_item_add_form.html',
            context={
                'form': form,
                'action': action
            },
            request=request
        )

        return JsonResponse({'html': html})

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.shop = self.request.user.shop
        self.object.save()

        html = render_to_string(
            'management/pricelist/includes/_pricelist_item.html',
            context={'pricelist_item': self.object},
            request=self.request
        )
        return JsonResponse({'html': html})

    def form_invalid(self, form):
        return JsonResponse(form.errors, status=400)


class PriceListItemEdit(ManagerTestMixin, UpdateView):
    models = PriceListItem
    form_class = PriceListItemForm
    queryset = PriceListItem.objects.all()

    def get_queryset(self):
        user = self.request.user
        shop = user.shop
        return shop.pricelist_items.all()

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)

        action = reverse(
            'management:pricelist-item-edit',
            args=(self.object.id,)
        )
        html = render_to_string(
            'management/pricelist/includes/_pricelist_item_edit_modal.html',
            context={
                'form': context['form'],
                'action': action
            },
            request=request
        )
        return JsonResponse({'html': html, 'image': self.object.get_image})

    def form_valid(self, form):
        self.object = form.save()
        html = render_to_string(
            'management/pricelist/includes/_pricelist_item.html',
            context={'pricelist_item': self.object},
            request=self.request
        )
        return JsonResponse({'html': html})

    def form_invalid(self, form):
        return JsonResponse(form.errors, status=400)


class AddPositionFromItem(ManagerTestMixin, DetailView):
    model = PriceListItem
    template_name = 'management/orders/includes/_position_formset_row.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        num_forms = self.request.GET.get('num_forms', 0)
        self.object.quantity = 1
        context = {
            'id': num_forms,
            'pricelist_item': self.object
        }
        html = render_to_string(
            self.template_name,
            context=context,
            request=request
        )
        response_dict = {
            'html': html,
            'item_price': self.object.price
        }
        return JsonResponse(response_dict)


class PriceListItemSearch(ManagerTestMixin, TemplateView):
    template_name = 'management/orders/includes/_pricelist_items.html'

    def get(self, request, *args, **kwargs):
        if 'application/json' in request.accepts():

            query = self.request.GET.get('q')
            source = self.request.GET.get('source', 'orders')

            if source == 'pricelist':
                template_name = 'management/pricelist/includes/_pricelist_items.html'
            else:
                template_name = self.template_name

            user = request.user
            shop = user.shop
            pricelist_items = PriceListItem.objects.filter(shop=shop)

            if query:
                pricelist_items = pricelist_items.filter(
                    Q(item_id__icontains=query) | Q(name__icontains=query)
                )

            html = render_to_string(
                template_name,
                {'pricelist_items': pricelist_items}
            )
            response_dict = {'html': html}
            return JsonResponse(response_dict)
        else:
            raise Http404()
