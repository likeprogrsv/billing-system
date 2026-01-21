from django.core.management.base import BaseCommand
from billing.models import Currency, Balance


class Command(BaseCommand):
    help = 'Initialize balances'

    def handle(self, *args, **options):
        for currency in Currency.objects.all():
            Balance.objects.get_or_create(currency=currency, amount=100_000)
