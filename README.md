# Бот для оптимизации Windows

Этот бот создает скрипты для оптимизации работы Windows на основе скриншота системной информации.

## Требования

- Python 3.6 или выше
- Установленные библиотеки из `requirements.txt`
- Ключи API для Telegram и Claude (Anthropic)

## Установка

1. Установите необходимые зависимости:
```
pip install -r requirements.txt
```

2. Создайте файл `.env` с вашими ключами API:
```
TELEGRAM_BOT_TOKEN=ваш_токен_бота
ANTHROPIC_API_KEY=ваш_ключ_API_Anthropic
```

3. Подготовьте структуру директорий:
```
mkdir -p data/prompts
```

## Запуск бота

### PowerShell
В PowerShell используйте следующий синтаксис:
```
cd bot_optimixation; python optimization_bot.py
```
или
```
cd bot_optimixation
python optimization_bot.py
```

### Командная строка (CMD)
```
cd bot_optimixation && python optimization_bot.py
```

## Деплой на Railway

Для деплоя бота на платформу Railway доступна подробная документация:

- [Инструкции по деплою на Railway (рус)](RAILWAY_DEPLOY.md) - полное руководство на русском языке
- [Railway Deployment Guide (eng)](RAILWAY_DEPLOY_EN.md) - complete guide in English
- [Быстрое решение проблемы с proxies](PROXIES_ISSUE_QUICKFIX.md) - быстрое исправление ошибки с параметром proxies

### Краткая инструкция:

1. Создайте аккаунт на [Railway](https://railway.app/)
2. Загрузите проект одним из способов:
   - **Через GitHub**: New Project → Deploy from GitHub repo
   - **Напрямую**: Используйте Railway CLI (`npm i -g @railway/cli`)
3. Настройте переменные окружения (`TELEGRAM_TOKEN`, `ANTHROPIC_API_KEY`)
4. Убедитесь, что файл `railway.json` содержит правильную команду запуска:
   ```json
   "startCommand": "python safe_anthropic.py && python optimization_bot.py"
   ```

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