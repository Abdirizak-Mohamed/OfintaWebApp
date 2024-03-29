# system
import requests

# django
from django.core.management import BaseCommand
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = 'Create initial test data'

    def handle(self, *args, **options):
        site = Site.objects.get_current()
        webhook_url = 'http://{}/mpesa-result/'.format(site.domain)
        response = requests.get(webhook_url, {})
        print(response.status_code)
