# Деплой оптимизатора на Railway

Этот документ содержит подробные инструкции по деплою бота для оптимизации Windows на платформу Railway, включая решение известной проблемы с параметром `proxies` в API Anthropic.

## Предварительные требования

- Аккаунт на [Railway](https://railway.app/)
- Ключ API Anthropic (Claude)
- Токен Telegram Bot API

## Шаги по деплою

### 1. Подготовка проекта

1. Убедитесь, что все необходимые файлы присутствуют в репозитории:
   - `optimization_bot.py` - основной файл бота
   - `safe_anthropic.py` - обертка для решения проблемы с proxies
   - `requirements.txt` - список зависимостей
   - `railway.json` - конфигурация для Railway

2. Проверьте содержимое `railway.json`:
   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "numReplicas": 1,
       "sleepApplication": false,
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10,
       "startCommand": "python safe_anthropic.py && python optimization_bot.py"
     }
   }
   ```

3. Проверьте, что в `requirements.txt` указана правильная версия библиотеки Anthropic:
   ```
   anthropic==0.19.0
   ```

### 2. Деплой через веб-интерфейс Railway

1. Войдите в свой аккаунт Railway
2. Нажмите на кнопку "New Project"
3. Выберите "Deploy from GitHub repo" и подключите свой репозиторий
4. После создания проекта, перейдите в раздел "Variables"
5. Добавьте следующие переменные окружения:
   - `TELEGRAM_TOKEN`: ваш токен бота Telegram
   - `ANTHROPIC_API_KEY`: ваш ключ API Anthropic
   - `RAILWAY_ENVIRONMENT`: `production`

### 3. Деплой через CLI

Альтернативно, можно выполнить деплой через командную строку:

1. Установите CLI Railway: 
   ```
   npm i -g @railway/cli
   ```

2. Войдите в аккаунт: 
   ```
   railway login
   ```

3. Свяжите локальную директорию с новым проектом: 
   ```
   railway init
   ```

4. Добавьте переменные окружения:
   ```
   railway variables set TELEGRAM_TOKEN=ваш_токен_бота
   railway variables set ANTHROPIC_API_KEY=ваш_ключ_API
   railway variables set RAILWAY_ENVIRONMENT=production
   ```

5. Выполните деплой:
   ```
   railway up
   ```

## Решение проблемы с параметром proxies

В Railway при работе с API Anthropic может возникать ошибка:
```
ERROR: __init__() got an unexpected keyword argument 'proxies'
```

Это происходит из-за того, что Railway автоматически добавляет параметр `proxies` в HTTP-клиенты, но библиотека Anthropic версии 0.19.0 не поддерживает этот параметр.

### Как работает наше решение:

1. Файл `safe_anthropic.py` перехватывает и удаляет параметр `proxies` при инициализации клиента Anthropic
2. В `railway.json` указана команда для запуска `safe_anthropic.py` перед основным ботом
3. В `optimization_bot.py` используется эта безопасная обертка вместо прямого импорта Anthropic

### Проверка логов

При возникновении проблем проверьте логи в консоли Railway. Если ошибка с `proxies` всё ещё появляется, убедитесь что:

1. Запуск происходит через команду в `railway.json`
2. В `optimization_bot.py` используется импорт `import safe_anthropic as anthropic`
3. Версия библиотеки Anthropic в `requirements.txt` соответствует 0.19.0

## Дополнительные материалы

- [Тест всех подходов к решению проблемы](test_all_fixes.py)
- [Документация Railway](https://docs.railway.app/)
- [API Anthropic](https://docs.anthropic.com/claude/reference/) 