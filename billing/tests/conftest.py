import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from billing.models import Currency, Balance


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def currencies(db):
    rub = Currency.objects.create(code='RUB', name='Russian Ruble')
    usd = Currency.objects.create(code='USD', name='US Dollar')
    return {'RUB': rub, 'USD': usd}


@pytest.fixture
def balances(currencies):
    rub_balance = Balance.objects.create(
        currency=currencies['RUB'],
        amount=Decimal('100000.00')
    )
    usd_balance = Balance.objects.create(
        currency=currencies['USD'],
        amount=Decimal('1000.00')
    )
    return {'RUB': rub_balance, 'USD': usd_balance}
