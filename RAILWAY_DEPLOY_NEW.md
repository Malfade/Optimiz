# Руководство по развертыванию на Railway с использованием fallback_anthropic

## Обзор

Это руководство описывает процесс развертывания Optimization Bot на платформе Railway с использованием `fallback_anthropic` - нашей собственной имплементации API Anthropic, которая решает проблемы с прокси.

## Преимущества этого подхода

1. Не требует установки официальной библиотеки `anthropic`
2. Обходит проблемы с прокси на платформе Railway
3. Поддерживает тот же интерфейс, что и оригинальная библиотека
4. Включает автоматический патчинг импортов через `fix_imports.py`

## Необходимые файлы

Для успешного развертывания требуются следующие файлы:

1. `main.py` - основной файл запуска, импортирующий `fix_imports.py`
2. `fix_imports.py` - система патчинга импортов
3. `fallback_anthropic.py` - наша реализация API Anthropic
4. `safe_anthropic.py` - безопасная обертка для API
5. `optimization_bot.py` - основной код бота
6. `requirements.txt` - зависимости без библиотеки `anthropic`
7. `Procfile` - инструкции для Railway о том, как запускать сервис

## Порядок действий для развертывания

### 1. Подготовка репозитория

1. Создайте новый репозиторий на GitHub или используйте существующий
2. Загрузите все необходимые файлы из списка выше
3. Убедитесь, что в `requirements.txt` нет зависимости от `anthropic`

### 2. Настройка проекта в Railway

1. Создайте аккаунт на [Railway.app](https://railway.app/)
2. Создайте новый проект, выбрав опцию "Deploy from GitHub repo"
3. Выберите ваш репозиторий
4. В разделе Variables добавьте переменные окружения:
   - `API_KEY` - ваш ключ API от Anthropic
   - `TELEGRAM_BOT_TOKEN` - токен вашего Telegram бота
   - `ALLOWED_USERS` - список ID пользователей, разделенных запятыми (опционально)

### 3. Развертывание

1. Railway автоматически обнаружит `Procfile` и начнет развертывание
2. После успешного развертывания проверьте логи на наличие сообщений об успешной инициализации:
   ```
   INFO:fix_imports:Запуск исправления импортов anthropic...
   INFO:fallback_anthropic:Fallback Anthropic модуль инициализирован
   INFO:fix_imports:🚀 Исправление импортов anthropic выполнено успешно!
   ```

### 4. Тестирование

1. Найдите свой бот в Telegram и отправьте команду `/start`
2. Проверьте, что бот отвечает на сообщения и может обрабатывать скриншоты

## Устранение неполадок

Если у вас возникли проблемы с развертыванием:

1. Проверьте логи в Railway на наличие ошибок
2. Убедитесь, что все переменные окружения установлены правильно
3. Проверьте, что файл `fix_imports.py` импортируется в `main.py` до любых других импортов
4. Запустите локально файл `test_fix_import.py` для проверки работы патчинга импортов

## Обновление и перезапуск

После внесения изменений в код:

1. Загрузите изменения в ваш GitHub репозиторий
2. Railway автоматически обнаружит изменения и перезапустит сервис
3. Проверьте логи, чтобы убедиться, что все работает корректно

## Дополнительные ресурсы

- [Документация Railway](https://docs.railway.app/)
- [Документация API Anthropic](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [Документация Python Telegram Bot](https://docs.python-telegram-bot.org/) 