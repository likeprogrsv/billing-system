import pytest
from decimal import Decimal
from billing.models import Transaction


@pytest.mark.django_db
class TestConversionAPI:

    def test_successful_rub_to_usd_conversion(self, api_client, balances):
        initial_rub = balances['RUB'].amount
        initial_usd = balances['USD'].amount

        data = {
            'sum': '100',
            'currency_id': 'USD',
            'gross_currency_id': 'RUB',
            'exchange_rate': '85.0'
        }

        # Act
        response = api_client.post('/api/transactions/conversion/', data, format='json')

        # Assert
        assert response.status_code == 201
        assert response.data['transaction_type'] == 'conversion'
        assert Decimal(response.data['amount']) == Decimal('100.00000')
        assert response.data['currency'] == 'USD'
        assert response.data['gross_currency'] == 'RUB'

        # Проверяем балансы
        balances['RUB'].refresh_from_db()
        balances['USD'].refresh_from_db()

        assert balances['RUB'].amount == initial_rub - Decimal('8500.00')  # 100 * 85
        assert balances['USD'].amount == initial_usd + Decimal('100.00')

        # Проверяем создание транзакции
        assert Transaction.objects.count() == 1
        txn = Transaction.objects.first()
        assert txn.transaction_type == 'conversion'
        assert txn.amount == Decimal('100.00000')

    def test_successful_usd_to_rub_conversion(self, api_client, balances):
        """Тест успешной конвертации USD → RUB"""
        initial_rub = balances['RUB'].amount
        initial_usd = balances['USD'].amount

        data = {
            'sum': '8500',
            'currency_id': 'RUB',
            'gross_currency_id': 'USD',
            'exchange_rate': '85.0'
        }

        response = api_client.post('/api/transactions/conversion/', data, format='json')

        assert response.status_code == 201
        assert response.data['currency'] == 'RUB'
        assert response.data['gross_currency'] == 'USD'

        balances['RUB'].refresh_from_db()
        balances['USD'].refresh_from_db()

        assert balances['RUB'].amount == initial_rub + Decimal('8500.00')
        assert balances['USD'].amount == initial_usd - Decimal('100.00')  # 8500 / 85

    def test_insufficient_funds(self, api_client, balances):
        """Тест недостаточности средств"""
        initial_rub = balances['RUB'].amount

        data = {
            'sum': '10000',  # Нужно 850000 RUB, но есть только 100000
            'currency_id': 'USD',
            'gross_currency_id': 'RUB',
            'exchange_rate': '85.0'
        }

        response = api_client.post('/api/transactions/conversion/', data, format='json')

        assert response.status_code == 400
        assert 'Недостаточно средств' in str(response.data)

        # Баланс не должен измениться
        balances['RUB'].refresh_from_db()
        assert balances['RUB'].amount == initial_rub

        # Транзакция не должна создаться
        assert Transaction.objects.count() == 0

    def test_same_currencies_error(self, api_client, balances):
        """Тест ошибки при одинаковых валютах"""
        data = {
            'sum': '100',
            'currency_id': 'RUB',
            'gross_currency_id': 'RUB',
            'exchange_rate': '85.0'
        }

        response = api_client.post('/api/transactions/conversion/', data, format='json')

        assert response.status_code == 400
        assert 'Валюты конвертации должны быть разными' in str(response.data)

    def test_negative_sum(self, api_client, balances):
        """Тест отрицательной суммы"""
        data = {
            'sum': '-100',
            'currency_id': 'USD',
            'gross_currency_id': 'RUB',
            'exchange_rate': '85.0'
        }

        response = api_client.post('/api/transactions/conversion/', data, format='json')

        assert response.status_code == 400
        assert 'sum' in response.data

    def test_zero_sum(self, api_client, balances):
        """Тест нулевой суммы"""
        data = {
            'sum': '0',
            'currency_id': 'USD',
            'gross_currency_id': 'RUB',
            'exchange_rate': '85.0'
        }

        response = api_client.post('/api/transactions/conversion/', data, format='json')

        assert response.status_code == 400
        assert 'sum' in response.data

    def test_invalid_currency(self, api_client, balances):
        """Тест несуществующей валюты"""
        data = {
            'sum': '100',
            'currency_id': 'EUR',
            'gross_currency_id': 'RUB',
            'exchange_rate': '85.0'
        }

        response = api_client.post('/api/transactions/conversion/', data, format='json')

        assert response.status_code == 400
        assert 'currency_id' in response.data

    def test_missing_required_fields(self, api_client, balances):
        """Тест отсутствия обязательных полей"""
        data = {
            'sum': '100',
            'currency_id': 'USD'
            # Отсутствуют gross_currency_id и exchange_rate
        }

        response = api_client.post('/api/transactions/conversion/', data, format='json')

        assert response.status_code == 400
        assert 'gross_currency_id' in response.data or 'exchange_rate' in response.data

    def test_case_insensitive_currency_codes(self, api_client, balances):
        """Тест нечувствительности к регистру кодов валют"""
        initial_rub = balances['RUB'].amount
        initial_usd = balances['USD'].amount

        data = {
            'sum': '10',
            'currency_id': 'usd',  # нижний регистр
            'gross_currency_id': 'rub',  # нижний регистр
            'exchange_rate': '85.0'
        }

        response = api_client.post('/api/transactions/conversion/', data, format='json')

        assert response.status_code == 201

        balances['RUB'].refresh_from_db()
        balances['USD'].refresh_from_db()

        assert balances['RUB'].amount == initial_rub - Decimal('850.00')
        assert balances['USD'].amount == initial_usd + Decimal('10.00')
