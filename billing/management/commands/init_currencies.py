from django.core.management.base import BaseCommand
from billing.models import Currency, Balance


class Command(BaseCommand):
    help = 'Initialize currencies'

    def handle(self, *args, **options):
        Currency.objects.get_or_create(code='USD', name='United States Dollar')
        Currency.objects.get_or_create(code='RUB', name='Russian Ruble')
