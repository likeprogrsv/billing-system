import pytest
from decimal import Decimal
from billing.models import Transaction


@pytest.mark.django_db
class TestServiceSpendAPI:
    """Тесты для API покупки услуг"""

    def test_service_spend_in_rub(self, api_client, balances):
        """Тест покупки услуги в RUB"""
        initial_rub = balances['RUB'].amount

        data = {
            'sum': '1000',
            'currency_id': 'RUB'
        }

        response = api_client.post('/api/transactions/service-spend/', data, format='json')

        assert response.status_code == 201
        assert response.data['transaction_type'] == 'service_spend'
        assert Decimal(response.data['amount']) == Decimal('1000.00000')
        assert response.data['currency'] == 'RUB'

        balances['RUB'].refresh_from_db()
        assert balances['RUB'].amount == initial_rub - Decimal('1000.00')

        assert Transaction.objects.count() == 1

    def test_service_spend_in_usd_with_conversion(self, api_client, balances):
        """Тест покупки услуги в USD с конвертацией из RUB"""
        initial_rub = balances['RUB'].amount

        data = {
            'sum': '50',
            'currency_id': 'USD',
            'gross_currency_id': 'RUB',
            'exchange_rate': '85.0'
        }

        response = api_client.post('/api/transactions/service-spend/', data, format='json')

        assert response.status_code == 201
        assert response.data['currency'] == 'USD'
        assert response.data['gross_currency'] == 'RUB'

        balances['RUB'].refresh_from_db()
        assert balances['RUB'].amount == initial_rub - Decimal('4250.00')  # 50 * 85

    def test_insufficient_funds_for_service(self, api_client, balances):
        """Тест недостаточности средств для покупки услуги"""
        data = {
            'sum': '200000',  # Больше чем есть на балансе
            'currency_id': 'RUB'
        }

        response = api_client.post('/api/transactions/service-spend/', data, format='json')

        assert response.status_code == 400
        assert 'Недостаточно средств' in str(response.data)
        assert Transaction.objects.count() == 0

    def test_service_spend_in_usd_without_conversion_fields(self, api_client, balances):
        """Тест покупки в USD без полей конвертации"""
        data = {
            'sum': '50',
            'currency_id': 'USD'
            # Отсутствуют gross_currency_id и exchange_rate
        }

        response = api_client.post('/api/transactions/service-spend/', data, format='json')

        assert response.status_code == 400
        assert 'необходимы поля gross_currency_id и exchange_rate' in str(response.data).lower()

    def test_negative_amount_service(self, api_client, balances):
        """Тест отрицательной суммы для услуги"""
        data = {
            'sum': '-100',
            'currency_id': 'RUB'
        }

        response = api_client.post('/api/transactions/service-spend/', data, format='json')

        assert response.status_code == 400
