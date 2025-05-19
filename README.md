# Optimizator

Оптимизатор для Windows на базе Claude от Anthropic.

## Особенности

- Автоматический анализ и оптимизация скриптов для Windows
- Интеграция с Claude API для генерации решений
- Поддержка работы через Telegram
- Специальная реализация для обхода проблем с прокси в Railway

## Обходной путь для проблем с прокси в Railway

В проекте реализован обходной путь для проблем с параметром `proxies` в библиотеке Anthropic при деплое на Railway:

1. Создан файл `fallback_anthropic.py` - минимальная реализация API Anthropic без использования оригинальной библиотеки
2. Реализован механизм подмены импортов через `fix_imports.py` - автоматически заменяет импорты оригинальной библиотеки на нашу реализацию
3. Обновлен `safe_anthropic.py` для совместимости с новым подходом

### Как использовать

1. При деплое на Railway:
   - Удалите библиотеку `anthropic` из `requirements.txt`
   - Импортируйте `fix_imports` перед любыми импортами `anthropic`
   - Используйте стандартный API Anthropic, как обычно

2. Пример использования:
   ```python
   # Сначала импортируем fix_imports
   import fix_imports
   
   # Теперь можно импортировать anthropic как обычно
   import anthropic
   
   # Создание клиента работает как с оригинальной библиотекой
   client = anthropic.Anthropic(api_key="your_api_key")
   
   # Отправка сообщений также работает стандартно
   response = client.messages.create(
       model="claude-3-haiku-20240307",
       max_tokens=1000,
       messages=[{"role": "user", "content": "Hello!"}]
   )
   ```

### Отладка

Для проверки корректной работы подмены импортов можно использовать скрипт `test_fix_import.py`:

```
python test_fix_import.py
```

Успешный вывод должен содержать:
```
INFO:fix_imports:✅ fallback_anthropic успешно импортирован
INFO:fix_imports:✅ fallback_anthropic успешно установлен как модуль anthropic
INFO:fix_imports:🚀 Исправление импортов anthropic выполнено успешно!
```

## Настройка и запуск

1. Установите зависимости:
   ```
   pip install -r requirements.txt
   ```

2. Настройте переменные окружения:
   ```
   ANTHROPIC_API_KEY=your_api_key
   TELEGRAM_BOT_TOKEN=your_bot_token
   ```

3. Запустите бот:
   ```
   python main.py
   ```

## Деплой на Railway

Подробные инструкции по деплою на Railway можно найти в файле `RAILWAY_RESTART.md`.

## Функции бота

- Создание скриптов оптимизации Windows на основе скриншота системы
- Исправление ошибок в существующих скриптах
- Показ статистики по сгенерированным скриптам
- Обновление шаблонов промптов на основе накопленных данных

## Команды бота

- `/start` - Начало работы с ботом
- `/help` - Помощь по использованию
- `/generate` - Сгенерировать новый скрипт оптимизации (нужно приложить фото)
- `/optimize` - Оптимизировать промпты (для администраторов)

## Устранение проблем

### Ошибка "Your credit balance is too low to access the Anthropic API"
Эта ошибка означает, что закончился баланс API-кредитов Anthropic. Бот автоматически переключится на использование шаблонных скриптов. Для полной функциональности необходимо пополнить баланс в аккаунте Anthropic.

### Ошибка запуска в PowerShell ("Лексема "&&" не является допустимым разделителем")
В PowerShell не работает оператор `&&` для объединения команд как в CMD. Используйте точку с запятой (`;`) или запускайте команды по отдельности:
```
cd bot_optimixation
python optimization_bot.py
```

Если при запуске скриптов возникают проблемы:

1. **Ошибки выполнения PowerShell**:
   - Убедитесь, что запускаете скрипт с правами администратора
   - Проверьте политику выполнения PowerShell: `Get-ExecutionPolicy`
   - При необходимости, измените политику: `Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process`

2. **Скрипт не запускается**:
   - Запустите командную строку от имени администратора
   - Перейдите в папку со скриптами: `cd путь_к_папке`
   - Запустите bat-файл вручную: `Start-Optimizer.bat`

3. **Система работает нестабильно после оптимизации**:
   - Все изменения фиксируются в логах, расположенных в `%USERPROFILE%\WindowsOptimizer_Logs`
   - Для откатов оптимизаций можно использовать точки восстановления системы
   - Резервные копии создаются в папке `%USERPROFILE%\WindowsOptimizer_Backups` 

## Исправление проблемы с proxies в Railway

Если вы столкнулись с ошибкой `__init__() got an unexpected keyword argument 'proxies'` при деплое на Railway, мы разработали несколько подходов для решения этой проблемы:

### Особенность версии Anthropic API 0.19.0

Обратите внимание, что в версии 0.19.0 библиотеки Anthropic (используемой в Railway) существует особенность: параметр `proxies` присутствует в сигнатуре метода `__init__`, но вызывает ошибку при фактическом использовании. Наши решения учитывают эту особенность.

### Решение 1: Safe Anthropic (Рекомендуемый)

Создает безопасную обертку для клиента Anthropic, которая удаляет параметр `proxies` перед передачей в оригинальный конструктор. Адаптировано для работы с версией 0.19.0.
ааа

**Использование в коде:**
```python
import safe_anthropic as anthropic
client = anthropic.Anthropic(api_key=your_key, proxies=any_proxies)  # proxies будет удален
```

**Или более безопасный способ:**
```python
import safe_anthropic 
client = safe_anthropic.create_client(api_key=your_key)  # не требует proxies
```

**Конфигурация в railway.json:**
```json
"startCommand": "python safe_anthropic.py && python optimization_bot.py"
```

### Решение 2: Anthropic Wrapper

Предоставляет альтернативный интерфейс к Anthropic API с аналогичным решением. Также адаптирован для версии 0.19.0.

**Использование в коде:**
```python
import anthropic_wrapper as anthropic
client = anthropic.Anthropic(api_key=your_key, proxies=any_proxies)  # proxies будет удален
```

**Или:**
```python
import anthropic_wrapper
client = anthropic_wrapper.create_client(api_key=your_key)
```

### Решение 3: Direct Fix

Патчит библиотеку Anthropic напрямую, изменяя конструктор класса `Anthropic`. Требует запуска перед основным скриптом.

**Конфигурация в railway.json:**
```json
"startCommand": "python direct_fix.py && python your_main_script.py"
```

## Тестирование

Все решения протестированы в скрипте `test_all_fixes.py`. Результаты показывают, что все методы успешно решают проблему с параметром `proxies`.

```
РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:
=======================
Базовая библиотека: ❌ НЕ РАБОТАЕТ С PROXIES (ОЖИДАЕМО)
direct_fix: ✅ УСПЕШНО
safe_anthropic: ✅ УСПЕШНО
anthropic_wrapper: ✅ УСПЕШНО
combined_approach: ✅ УСПЕШНО
```

## Рекомендации

Используйте `safe_anthropic` как самый надежный и простой метод обхода проблемы с proxies в Anthropic API. Для максимальной надежности используйте функцию `create_client()` вместо прямого создания экземпляра класса.

## Поддерживаемые версии

Решение протестировано и работает с:
- Anthropic API версии 0.19.0 (используется в Railway)
- Anthropic API версии 0.51.0 (локальная разработка)