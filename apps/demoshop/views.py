# django
from django.views.generic import TemplateView

# ofinta
from apps.demoshop.models import DemoProduct


class Demoshop(TemplateView):
    template_name = 'demoshop/demoshop.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['products'] = DemoProduct.objects.all()
        return context
