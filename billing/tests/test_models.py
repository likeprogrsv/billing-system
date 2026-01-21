import pytest
from decimal import Decimal
from billing.models import Balance, Currency, Transaction


@pytest.mark.django_db
class TestBalanceModel:
    """Тесты для методов модели Balance"""

    def test_deposit_increases_balance(self, currencies):
        """Тест метода deposit() - увеличивает баланс"""
        balance = Balance.objects.create(
            currency=currencies['RUB'],
            amount=Decimal('1000.00')
        )

        balance.deposit(Decimal('500.00'))

        assert balance.amount == Decimal('1500.00')

    def test_withdraw_decreases_balance(self, currencies):
        """Тест метода withdraw() - уменьшает баланс"""
        balance = Balance.objects.create(
            currency=currencies['RUB'],
            amount=Decimal('1000.00')
        )

        balance.withdraw(Decimal('300.00'))

        assert balance.amount == Decimal('700.00')

    def test_check_sufficient_balance_passes_when_enough(self, currencies):
        """Тест check_sufficient_balance() - достаточно средств"""
        balance = Balance.objects.create(
            currency=currencies['RUB'],
            amount=Decimal('1000.00')
        )

        # Не должно выбросить исключение
        balance.check_sufficient_balance(Decimal('999.99'))
        balance.check_sufficient_balance(Decimal('1000.00'))

    def test_check_sufficient_balance_fails_when_not_enough(self, currencies):
        """Тест check_sufficient_balance() - недостаточно средств"""
        balance = Balance.objects.create(
            currency=currencies['RUB'],
            amount=Decimal('1000.00')
        )

        with pytest.raises(ValueError, match="Недостаточно средств"):
            balance.check_sufficient_balance(Decimal('1000.01'))

    def test_deposit_preserves_decimal_precision(self, currencies):
        """Тест что deposit() сохраняет точность Decimal"""
        balance = Balance.objects.create(
            currency=currencies['RUB'],
            amount=Decimal('100.00')
        )

        balance.deposit(Decimal('0.01'))

        assert balance.amount == Decimal('100.01')
        assert isinstance(balance.amount, Decimal)

    def test_withdraw_preserves_decimal_precision(self, currencies):
        """Тест что withdraw() сохраняет точность Decimal"""
        balance = Balance.objects.create(
            currency=currencies['RUB'],
            amount=Decimal('100.00')
        )

        balance.withdraw(Decimal('0.01'))

        assert balance.amount == Decimal('99.99')
        assert isinstance(balance.amount, Decimal)

    def test_multiple_deposits(self, currencies):
        """Тест нескольких последовательных пополнений"""
        balance = Balance.objects.create(
            currency=currencies['RUB'],
            amount=Decimal('0.00')
        )

        balance.deposit(Decimal('100.00'))
        balance.deposit(Decimal('200.00'))
        balance.deposit(Decimal('50.50'))

        assert balance.amount == Decimal('350.50')

    def test_multiple_withdrawals(self, currencies):
        """Тест нескольких последовательных списаний"""
        balance = Balance.objects.create(
            currency=currencies['RUB'],
            amount=Decimal('1000.00')
        )

        balance.withdraw(Decimal('100.00'))
        balance.withdraw(Decimal('200.00'))
        balance.withdraw(Decimal('50.50'))

        assert balance.amount == Decimal('649.50')

    def test_deposit_and_withdraw_combination(self, currencies):
        """Тест комбинации пополнений и списаний"""
        balance = Balance.objects.create(
            currency=currencies['RUB'],
            amount=Decimal('1000.00')
        )

        balance.deposit(Decimal('500.00'))
        balance.withdraw(Decimal('300.00'))
        balance.deposit(Decimal('100.00'))

        assert balance.amount == Decimal('1300.00')


@pytest.mark.django_db
class TestTransactionModel:
    """Тесты для модели Transaction"""

    def test_transaction_creation_with_all_fields(self, currencies):
        """Тест создания транзакции со всеми полями"""
        txn = Transaction.objects.create(
            transaction_type=Transaction.TransactionType.CONVERSION,
            amount=Decimal('100.00000'),
            currency=currencies['USD'],
            gross_currency=currencies['RUB'],
            exchange_rate=Decimal('85.0')
        )

        assert txn.transaction_type == 'conversion'
        assert txn.amount == Decimal('100.00000')
        assert txn.currency.code == 'USD'
        assert txn.gross_currency.code == 'RUB'
        assert txn.exchange_rate == Decimal('85.0')
        assert txn.created_at is not None

    def test_transaction_creation_without_optional_fields(self, currencies):
        """Тест создания транзакции без опциональных полей"""
        txn = Transaction.objects.create(
            transaction_type=Transaction.TransactionType.SERVICE_SPEND,
            amount=Decimal('500.00000'),
            currency=currencies['RUB']
        )

        assert txn.transaction_type == 'service_spend'
        assert txn.amount == Decimal('500.00000')
        assert txn.currency.code == 'RUB'
        assert txn.gross_currency is None
        assert txn.exchange_rate is None

    def test_transaction_type_display(self, currencies):
        """Тест отображения типа транзакции"""
        txn_conversion = Transaction.objects.create(
            transaction_type=Transaction.TransactionType.CONVERSION,
            amount=Decimal('100.00000'),
            currency=currencies['USD']
        )

        txn_spend = Transaction.objects.create(
            transaction_type=Transaction.TransactionType.SERVICE_SPEND,
            amount=Decimal('500.00000'),
            currency=currencies['RUB']
        )

        txn_topup = Transaction.objects.create(
            transaction_type=Transaction.TransactionType.ACCOUNT_TOPUP,
            amount=Decimal('1000.00000'),
            currency=currencies['RUB']
        )

        assert txn_conversion.get_transaction_type_display() == "Конвертация валюты"
        assert txn_spend.get_transaction_type_display() == "Покупка услуги"
        assert txn_topup.get_transaction_type_display() == "Пополнение аккаунта"

    def test_transaction_str_representation(self, currencies):
        """Тест строкового представления транзакции"""
        txn = Transaction.objects.create(
            transaction_type=Transaction.TransactionType.CONVERSION,
            amount=Decimal('100.00000'),
            currency=currencies['USD']
        )

        str_repr = str(txn)
        assert 'Конвертация валюты' in str_repr
        assert '100' in str_repr


@pytest.mark.django_db
class TestCurrencyModel:
    """Тесты для модели Currency"""

    def test_currency_creation(self):
        """Тест создания валюты"""
        currency = Currency.objects.create(
            code='EUR',
            name='Euro'
        )

        assert currency.code == 'EUR'
        assert currency.name == 'Euro'

    def test_currency_str_representation(self):
        """Тест строкового представления валюты"""
        currency = Currency.objects.create(code='EUR', name='Euro')

        assert str(currency) == 'EUR'

    def test_currency_code_is_primary_key(self):
        """Тест что code является первичным ключом"""
        eur = Currency.objects.create(code='EUR', name='Euro')

        # Попытка создать ещё одну валюту с тем же кодом должна вызвать ошибку
        with pytest.raises(Exception):
            Currency.objects.create(code='EUR', name='Euro 2')
