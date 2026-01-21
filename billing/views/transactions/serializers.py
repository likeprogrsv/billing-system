from decimal import Decimal, InvalidOperation
from rest_framework import serializers
from billing.models import Transaction, Currency, Balance


class TransactionSerializer(serializers.Serializer):
    sum = serializers.CharField(required=True)
    currency_id = serializers.CharField(required=True)
    gross_currency_id = serializers.CharField(required=False, allow_null=True)
    exchange_rate = serializers.CharField(required=False, allow_null=True)

    def validate_sum(self, value):
        try:
            amount = Decimal(value)
        except (InvalidOperation, ValueError):
            raise serializers.ValidationError("Некорректное значение суммы")

        if amount <= 0:
            raise serializers.ValidationError("Сумма должна быть больше 0")

        return amount

    def validate_exchange_rate(self, value):
        if value is None:
            return None

        try:
            rate = Decimal(value)
        except (InvalidOperation, ValueError):
            raise serializers.ValidationError("Некорректное значение обменного курса")

        if rate <= 0:
            raise serializers.ValidationError("Обменный курс должен быть больше 0")

        return rate

    def _get_currency(self, value):
        currency_code = value.upper()
        try:
            return Currency.objects.get(code=currency_code)
        except Currency.DoesNotExist:
            raise serializers.ValidationError(f"Валюта {currency_code} не поддерживается")

    def validate_currency_id(self, value):
        if not value:
            raise serializers.ValidationError("Валюта обязательна")

        return self._get_currency(value)

    def validate_gross_currency_id(self, value):
        if not value:
            return None

        return self._get_currency(value)

    def _validate_non_rub_conversion(self, attrs):
        if attrs['currency_id'].code != 'RUB':
            if not attrs.get('gross_currency_id') or not attrs.get('exchange_rate'):
                raise serializers.ValidationError(
                    "Для операции в валюте отличной от RUB необходимы поля gross_currency_id и exchange_rate"
                    )

    def validate(self, attrs):
        # Проверяем, что currency_id и gross_currency_id разные (если оба указаны)
        if attrs.get('gross_currency_id') and attrs.get('currency_id'):
            if attrs['gross_currency_id'].code == attrs['currency_id'].code:
                raise serializers.ValidationError(
                    "Валюты конвертации должны быть разными"
                )

        return attrs

    def create(self, validated_data):
        raise NotImplementedError("Метод create должен быть переопределён")


class ConversionSerializer(TransactionSerializer):
    gross_currency_id = serializers.CharField(required=True)
    exchange_rate = serializers.CharField(required=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)

        # Проверяем обязательные поля
        if not attrs.get('gross_currency_id'):
            raise serializers.ValidationError("Поле gross_currency_id обязательно для конвертации")

        if not attrs.get('exchange_rate'):
            raise serializers.ValidationError("Поле exchange_rate обязательно для конвертации")

        return attrs


class ServiceSpendSerializer(TransactionSerializer):
    def validate(self, attrs):
        attrs = super().validate(attrs)
        self._validate_non_rub_conversion(attrs)
        return attrs


class AccountTopUpSerializer(TransactionSerializer):
    def validate(self, attrs):
        attrs = super().validate(attrs)
        self._validate_non_rub_conversion(attrs)
        return attrs
