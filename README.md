# Billing System

Мини-система биллинга с поддержкой транзакций и управления балансом клиента.

## Описание проекта

Система предоставляет API для работы с финансовыми операциями:
- Конвертация валюты (RUB ↔ USD)
- Покупка услуг
- Пополнение счета

**Стек технологий:**
- Python 3.12
- Django 4.2
- Django REST Framework
- SQLite (для разработки)

## Инициализация проекта

### Требования

- Python 3.12 или выше
- [uv](https://github.com/astral-sh/uv)

### Установка uv

Если у вас еще не установлен `uv`, установите его:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Или через pip:
```bash
pip install uv
```

### Установка

1. **Клонируйте репозиторий** (если необходимо):
   ```bash
   git clone <repository-url>
   cd billing-system
   ```

2. **Создайте виртуальное окружение**:
   ```bash
   uv venv
   ```

3. **Активируйте виртуальное окружение**:

   На Linux/macOS:
   ```bash
   source .venv/bin/activate
   ```

   На Windows:
   ```bash
   .venv\Scripts\activate
   ```

4. **Установите зависимости**:
   ```bash
   uv pip install -r requirements.txt
   ```

5. **Примените миграции базы данных**:
   ```bash
   python manage.py migrate
   ```

6. **Инициализируйте валюты**:
   ```bash
   python manage.py init_currencies
   ```

   Эта команда создаст базовые валюты в системе:
   - USD (United States Dollar)
   - RUB (Russian Ruble)

7. **Создайте начальные балансы**:
   ```bash
   python manage.py init_balances
   ```

   Эта команда создаст балансы для каждой валюты с начальной суммой 100,000 единиц.
   Балансы создаются автоматически для всех существующих валют в системе.

### Запуск сервера разработки

После инициализации проекта вы можете запустить сервер разработки:

```bash
python manage.py runserver
```

Сервер будет доступен по адресу: http://127.0.0.1:8000/

### Примечания

- База данных SQLite создается автоматически при первом запуске миграций
- Команды `init_currencies` и `init_balances` используют `get_or_create`, поэтому их можно запускать многократно без создания дубликатов
- Команду `init_balances` нужно запускать после `init_currencies`, так как балансы создаются для существующих валют
- Для production окружения рекомендуется использовать PostgreSQL или другую production-ready базу данных

---

## Модели данных

### Currency (Валюта)
Справочник валют системы.

```python
- code: CharField (PK) - Код валюты (например, "USD", "RUB")
- name: CharField - Название валюты
```

### Balance (Баланс)
Хранит баланс для каждой валюты.

```python
- amount: DecimalField(20, 2) - Сумма на балансе
- currency: ForeignKey(Currency) - Валюта баланса
```

**Методы:**
- `deposit(amount)` - Пополнение баланса
- `withdraw(amount)` - Списание с баланса
- `check_sufficient_balance(amount)` - Проверка достаточности средств

### Transaction (Транзакция)
Записи о всех финансовых операциях.

```python
- transaction_type: CharField - Тип транзакции (conversion, service_spend, account_topup)
- amount: DecimalField(20, 5) - Сумма операции
- currency: ForeignKey(Currency) - Валюта операции
- gross_currency: ForeignKey(Currency, nullable) - Исходная валюта (для конвертации)
- exchange_rate: DecimalField(35, 16, nullable) - Обменный курс
- user: ForeignKey(User, nullable) - Пользователь
- created_at: DateTimeField - Дата и время создания
```

---

## API Эндпоинты

### 1. Конвертация валюты

**Эндпоинт:** `POST /api/transactions/conversion/`

**Описание:** Конвертирует валюту между RUB и USD с обновлением балансов.

**Обязательные поля:** `sum`, `currency_id`, `gross_currency_id`, `exchange_rate`

**Пример (RUB → USD):**
```bash
curl -X POST http://localhost:8000/api/transactions/conversion/ \
  -H "Content-Type: application/json" \
  -d '{"sum": "100", "currency_id": "USD", "gross_currency_id": "RUB", "exchange_rate": "85.0"}'
```

**Логика:** Списывает средства с исходной валюты, начисляет на целевую. Проверяет достаточность средств. Работает в транзакции БД с блокировкой записей.

### 2. Покупка услуги

**Эндпоинт:** `POST /api/transactions/service-spend/`

**Описание:** Списывает средства за покупку услуги. Все услуги продаются в RUB.

**Обязательные поля:** `sum`, `currency_id` (+ `gross_currency_id` и `exchange_rate` для не-RUB)

**Пример:**
```bash
curl -X POST http://localhost:8000/api/transactions/service-spend/ \
  -H "Content-Type: application/json" \
  -d '{"sum": "1000", "currency_id": "RUB"}'
```

**Логика:** Списывает с RUB баланса. Для операций не в RUB выполняется встроенная конвертация (`sum × exchange_rate`).

### 3. Пополнение счета

**Эндпоинт:** `POST /api/transactions/account-topup/`

**Описание:** Пополняет баланс. Все пополнения идут в RUB.

**Обязательные поля:** `sum`, `currency_id` (+ `gross_currency_id` и `exchange_rate` для не-RUB)

**Пример:**
```bash
curl -X POST http://localhost:8000/api/transactions/account-topup/ \
  -H "Content-Type: application/json" \
  -d '{"sum": "5000", "currency_id": "RUB"}'
```

**Логика:** Начисляет на RUB баланс. Для операций не в RUB выполняется встроенная конвертация (`sum × exchange_rate`).

---

## Валидация данных

Все эндпоинты выполняют следующие проверки:

### Валидация полей
- **sum**: обязательно, должно быть > 0, корректное Decimal значение
- **exchange_rate**: должно быть > 0 (если указано), корректное Decimal значение
- **currency_id / gross_currency_id**:
  - Не чувствительны к регистру (rub, RUB → RUB)
  - Должны существовать в БД
  - Должны быть разными (при конвертации)

### Бизнес-логика
- Проверка достаточности средств перед списанием
- Атомарность транзакций (через `transaction.atomic()`)
- Блокировка балансов при обновлении (`select_for_update()`)
- Обязательность `gross_currency_id` и `exchange_rate` для операций не в RUB

---

## Реализованный функционал

### ✅ Модели
- Модель `Currency` с кодом валюты как Primary Key
- Модель `Balance` с поддержкой методов `deposit()`, `withdraw()`, `check_sufficient_balance()`
- Модель `Transaction` со всеми необходимыми полями
- Связь с моделью `User` (опционально)

### ✅ API
- Эндпоинт конвертации валюты (`/api/transactions/conversion/`)
- Эндпоинт покупки услуги (`/api/transactions/service-spend/`)
- Эндпоинт пополнения счета (`/api/transactions/account-topup/`)
- Поддержка конвертации RUB ↔ USD
- Встроенная конвертация для операций не в RUB

### ✅ Валидация
- Проверка корректности сумм и обменных курсов
- Валидация существования валют
- Проверка различия валют при конвертации
- Нечувствительность к регистру кодов валют
- Проверка достаточности средств

### ✅ Безопасность и надежность
- Атомарные транзакции БД
- Блокировка записей при обновлении балансов
- Обработка ошибок с понятными сообщениями
- Использование Decimal для финансовых расчетов

### ✅ Архитектура
- Базовый класс `BaseTransactionView` для переиспользования кода
- Отдельные сериализаторы для каждого типа транзакции
- DRY принцип (отсутствие дублирования кода)
- Management commands для инициализации данных

### ✅ Документация
- README с инструкциями по установке
- Описание моделей данных
- Документация API с примерами
- Примеры curl запросов

### ✅ Тесты (34 теста)
- Тесты API эндпоинтов (18 тестов)
- Unit-тесты для методов моделей (16 тестов)

---



## Обработка ошибок

### Недостаточно средств
```json
{
  "error": "Недостаточно средств. Доступно: 1000.00 RUB"
}
```

### Некорректная сумма
```json
{
  "sum": ["Сумма должна быть больше 0"]
}
```

### Несуществующая валюта
```json
{
  "currency_id": ["Валюта EUR не поддерживается"]
}
```

### Одинаковые валюты при конвертации
```json
{
  "non_field_errors": ["Валюты конвертации должны быть разными"]
}
```

---


## Тестирование

**34 автоматических теста** (pytest + pytest-django) покрывают API и модели.

```bash
# Запуск всех тестов
pytest

# С подробным выводом
pytest -v

# Конкретная категория
pytest billing/tests/test_models.py -v
```

**Покрытие:**
- **API тесты (18):** Conversion, Service Spend, Account Top-Up
- **Model тесты (16):** Balance методы, Transaction, Currency

Подробнее: `TESTING.md`

---
