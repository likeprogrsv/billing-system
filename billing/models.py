from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class Currency(models.Model):
    """Модель валюты."""

    code = models.CharField(
        max_length=5,
        primary_key=True,
        verbose_name="Код валюты",
    )
    name = models.CharField(
        max_length=50,
        verbose_name="Название валюты",
        blank=True,
    )

    class Meta:
        verbose_name = "Валюта"
        verbose_name_plural = "Валюты"

    def __str__(self):
        return self.code


class Transaction(models.Model):
    """
    Модель транзакций клиентов.
    Описывает финансовые операции, связанные с клиентами.
    """
    class TransactionType(models.TextChoices):
        CONVERSION = "conversion", "Конвертация валюты"
        SERVICE_SPEND = "service_spend", "Покупка услуги"
        ACCOUNT_TOPUP = "account_topup", "Пополнение аккаунта"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name="Пользователь",
        null=True,
        blank=True,
    )
    transaction_type = models.CharField(verbose_name="Тип транзакции", max_length=50, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=20, decimal_places=5, verbose_name="Сумма")
    currency = models.ForeignKey(
        "Currency", on_delete=models.PROTECT,
        verbose_name="Валюта",
        related_name="currency_transactions",
    )

    # Поля для конвертации валют
    gross_currency = models.ForeignKey(
        "Currency",
        on_delete=models.PROTECT,
        verbose_name="Валюта для обмена",
        related_name="gross_currency_transactions",
        null=True,
        blank=True,
    )
    exchange_rate = models.DecimalField(
        max_digits=35,
        decimal_places=16,
        verbose_name="Обменный курс",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания записи")
    class Meta:
        verbose_name = "Транзакция"
        verbose_name_plural = "Транзакции"

    def __str__(self):
        return f"{self.pk} {self.get_transaction_type_display()} {self.amount}"

    def get_transaction_type_display(self):
        return self.TransactionType(self.transaction_type).label


class Balance(models.Model):
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        verbose_name="Баланс",
        default=0,
    )
    currency = models.ForeignKey(
        'Currency',
        on_delete=models.PROTECT,
        verbose_name="Валюта",
        related_name="balances",
    )

    class Meta:
        verbose_name = "Баланс"
        verbose_name_plural = "Балансы"

    def __str__(self):
        return f"{self.amount} {self.currency.code}"

    def check_sufficient_balance(self, amount):
        if self.amount < amount:
            raise ValueError(
                f"Недостаточно средств. Доступно: {self.amount} {self.currency.code}"
            )

    def withdraw(self, amount):
        assert isinstance(amount, Decimal)
        assert amount > 0

        self.check_sufficient_balance(amount)
        self.amount -= amount
        self.save()

    def deposit(self, amount):
        assert isinstance(amount, Decimal)
        assert amount > 0

        self.amount += amount
        self.save()
