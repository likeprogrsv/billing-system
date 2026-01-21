import pytest
from decimal import Decimal
from billing.models import Transaction


@pytest.mark.django_db
class TestAccountTopUpAPI:
    """Тесты для API пополнения счета"""

    def test_topup_in_rub(self, api_client, balances):
        """Тест пополнения в RUB"""
        initial_rub = balances['RUB'].amount

        data = {
            'sum': '5000',
            'currency_id': 'RUB'
        }

        response = api_client.post('/api/transactions/account-topup/', data, format='json')

        assert response.status_code == 201
        assert response.data['transaction_type'] == 'account_topup'
        assert Decimal(response.data['amount']) == Decimal('5000.00000')
        assert response.data['currency'] == 'RUB'

        balances['RUB'].refresh_from_db()
        assert balances['RUB'].amount == initial_rub + Decimal('5000.00')

        assert Transaction.objects.count() == 1

    def test_topup_in_usd_with_conversion(self, api_client, balances):
        """Тест пополнения в USD с конвертацией в RUB"""
        initial_rub = balances['RUB'].amount

        data = {
            'sum': '100',
            'currency_id': 'USD',
            'gross_currency_id': 'RUB',
            'exchange_rate': '85.0'
        }

        response = api_client.post('/api/transactions/account-topup/', data, format='json')

        assert response.status_code == 201
        assert response.data['currency'] == 'USD'
        assert response.data['gross_currency'] == 'RUB'

        balances['RUB'].refresh_from_db()
        assert balances['RUB'].amount == initial_rub + Decimal('8500.00')  # 100 * 85

    def test_topup_in_usd_without_conversion_fields(self, api_client, balances):
        """Тест пополнения в USD без полей конвертации"""
        data = {
            'sum': '100',
            'currency_id': 'USD'
        }

        response = api_client.post('/api/transactions/account-topup/', data, format='json')

        assert response.status_code == 400
        assert 'необходимы поля gross_currency_id и exchange_rate' in str(response.data).lower()

    def test_negative_amount_topup(self, api_client, balances):
        """Тест отрицательной суммы для пополнения"""
        data = {
            'sum': '-1000',
            'currency_id': 'RUB'
        }

        response = api_client.post('/api/transactions/account-topup/', data, format='json')

        assert response.status_code == 400
