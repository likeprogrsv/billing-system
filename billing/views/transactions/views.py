from decimal import Decimal

from django.db import transaction
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from billing.models import Transaction, Balance, Currency
from billing.views.transactions.serializers import ConversionSerializer, ServiceSpendSerializer, AccountTopUpSerializer


class BaseTransactionView(APIView):
    serializer_class = None
    transaction_type = None

    def post(self, request):
        # user = request.user # TODO: в будущем можно добавить юзера, для экономии времени не стал
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                result = self.process_transaction(serializer.validated_data)
                return Response(result, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Ошибка при обработке транзакции: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def process_transaction(self, validated_data, user=None):
        raise NotImplementedError("Метод process_transaction должен быть переопределён")

    def get_balance(self, currency):
        try:
            return Balance.objects.select_for_update().get(currency=currency)
        except Balance.DoesNotExist:
            raise ValueError(f"Баланс для валюты {currency.code} не найден")

    def create_transaction(
            self,
            transaction_type,
            amount,
            currency,
            gross_currency=None,
            exchange_rate=None,
            user=None,
        ) -> Transaction:
        return Transaction.objects.create(
            transaction_type=transaction_type,
            amount=amount,
            currency=currency,
            gross_currency=gross_currency,
            exchange_rate=exchange_rate,
            user=user,
        )


class ConversionView(BaseTransactionView):
    serializer_class = ConversionSerializer
    transaction_type = Transaction.TransactionType.CONVERSION

    def process_transaction(self, validated_data, user=None):
        amount = validated_data['sum']
        target_currency = validated_data['currency_id']
        source_currency = validated_data['gross_currency_id']
        exchange_rate = validated_data['exchange_rate']

        source_balance = self.get_balance(source_currency)
        target_balance = self.get_balance(target_currency)

        if source_currency.code == 'RUB' and target_currency.code != 'RUB':
            rub_to_deduct = amount * exchange_rate
            source_balance.check_sufficient_balance(rub_to_deduct)
            source_balance.withdraw(rub_to_deduct)
            target_balance.deposit(amount)
        elif source_currency.code != 'RUB' and target_currency.code == 'RUB':
            amount_to_deduct = amount / exchange_rate
            source_balance.check_sufficient_balance(amount_to_deduct)

            source_balance.withdraw(amount_to_deduct)
            target_balance.deposit(amount)
        txn = self.create_transaction(
            transaction_type=self.transaction_type,
            amount=amount,
            currency=target_currency,
            gross_currency=source_currency,
            exchange_rate=exchange_rate,
            user=user,
        )

        return {
            "id": txn.id,
            "transaction_type": txn.transaction_type,
            "amount": str(txn.amount),
            "currency": txn.currency.code,
            "gross_currency": txn.gross_currency.code,
            "exchange_rate": str(txn.exchange_rate),
            "created_at": txn.created_at,
            "balances": {
                source_currency.code: str(source_balance.amount),
                target_currency.code: str(target_balance.amount)
            }
        }


class ServiceSpendView(BaseTransactionView):
    serializer_class = ServiceSpendSerializer
    transaction_type = Transaction.TransactionType.SERVICE_SPEND

    def process_transaction(self, validated_data, user=None):
        amount = validated_data['sum']
        currency = validated_data['currency_id']
        gross_currency = validated_data.get('gross_currency_id')
        exchange_rate = validated_data.get('exchange_rate')

        rub_balance = self.get_balance(Currency.objects.get(code='RUB'))

        if currency.code == 'RUB':
            rub_balance.check_sufficient_balance(amount)
            rub_balance.withdraw(amount)
        else:
            if not gross_currency or not exchange_rate:
                raise ValueError("Для покупки в валюте, отличной от RUB, необходимы gross_currency_id и exchange_rate")

            rub_to_deduct = amount * exchange_rate
            rub_balance.check_sufficient_balance(rub_to_deduct)
            rub_balance.withdraw(rub_to_deduct)

        txn = self.create_transaction(
            transaction_type=self.transaction_type,
            amount=amount,
            currency=currency,
            gross_currency=gross_currency,
            exchange_rate=exchange_rate,
            user=user,
        )

        return {
            "id": txn.id,
            "transaction_type": txn.transaction_type,
            "amount": str(txn.amount),
            "currency": txn.currency.code,
            "gross_currency": txn.gross_currency.code if txn.gross_currency else None,
            "exchange_rate": str(txn.exchange_rate) if txn.exchange_rate else None,
            "created_at": txn.created_at,
            "balances": {
                "RUB": str(rub_balance.amount)
            }
        }


class TopUpView(BaseTransactionView):
    serializer_class = AccountTopUpSerializer
    transaction_type = Transaction.TransactionType.ACCOUNT_TOPUP

    def process_transaction(self, validated_data, user=None):
        amount = validated_data['sum']
        currency = validated_data['currency_id']
        gross_currency = validated_data.get('gross_currency_id')
        exchange_rate = validated_data.get('exchange_rate')

        rub_balance = self.get_balance(Currency.objects.get(code='RUB'))

        if currency.code == 'RUB':
            rub_balance.deposit(amount)
        else:
            if not gross_currency or not exchange_rate:
                raise ValueError("Для пополнения в валюте, отличной от RUB, необходимы gross_currency_id и exchange_rate")
            rub_balance.deposit(amount * exchange_rate)

        txn = self.create_transaction(
            transaction_type=self.transaction_type,
            amount=amount,
            currency=currency,
            gross_currency=gross_currency,
            exchange_rate=exchange_rate,
            user=user,
        )

        return {
            "id": txn.id,
            "transaction_type": txn.transaction_type,
            "amount": str(txn.amount),
            "currency": txn.currency.code,
            "gross_currency": txn.gross_currency.code if txn.gross_currency else None,
            "exchange_rate": str(txn.exchange_rate) if txn.exchange_rate else None,
            "created_at": txn.created_at,
            "balances": {
                "RUB": str(rub_balance.amount)
            }
        }
