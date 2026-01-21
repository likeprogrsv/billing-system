# billing-system

## Инициализация проекта

### Требования

- Python 3.12 или выше
- [uv](https://github.com/astral-sh/uv) (быстрый менеджер пакетов Python)

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
