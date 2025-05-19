# Пошаговая инструкция по деплою Telegram бота с Claude API на Railway

## Подготовка к деплою

1. Убедитесь, что у вас есть:
   - Аккаунт в [Railway](https://railway.app/)
   - Токен Telegram бота (получен через @BotFather)
   - API ключ Claude от Anthropic

2. Убедитесь, что в вашем коде:
   - Используется `import anthropic_wrapper as anthropic` (не прямой импорт)
   - Настроен файл `railway.json` с верными параметрами
   - Есть файл `Procfile` с командой запуска вашего бота

## Шаги для деплоя на Railway

1. **Подготовьте репозиторий для деплоя**:
   - Убедитесь, что файл `.env` добавлен в `.gitignore` (не выкладывайте свои API ключи!)
   - Проверьте, что `requirements.txt` содержит все необходимые зависимости
   - Проверьте, что версия anthropic точно указана: `anthropic==0.19.0`

2. **Через веб-интерфейс Railway**:
   - Войдите в свой аккаунт Railway
   - Создайте новый проект (New Project)
   - Выберите "Deploy from GitHub repo"
   - Подключите свой репозиторий
   - После создания проекта, перейдите в раздел "Variables"
   - Добавьте следующие переменные окружения:
     - `TELEGRAM_TOKEN`: ваш токен телеграм бота
     - `ANTHROPIC_API_KEY`: ваш API ключ от Claude
     - `RAILWAY_ENVIRONMENT`: `production`

3. **Или через CLI Railway**:
   - Установите CLI: `npm i -g @railway/cli`
   - Войдите в аккаунт: `railway login`
   - Привяжите локальную папку к проекту: `railway init`
   - Добавьте переменные окружения:
     ```
     railway variables set TELEGRAM_TOKEN=ваш_бот_токен
     railway variables set ANTHROPIC_API_KEY=ваш_api_ключ
     railway variables set RAILWAY_ENVIRONMENT=production
     ```
   - Деплой: `railway up`

## Решение проблемы с `proxies` параметром

Railway автоматически добавляет параметр `proxies` в HTTP клиенты, но библиотека Anthropic версии 0.19.0 не поддерживает этот параметр. Для решения этой проблемы:

1. Используйте обертку `safe_anthropic.py` или `anthropic_wrapper.py`, которая перехватывает и удаляет параметр `proxies` при инициализации клиента.

2. В `railway.json` указана команда запуска:
   ```json
   "startCommand": "python safe_anthropic.py && python optimization_bot.py"
   ```
   
   Это позволяет сначала применить патч к библиотеке Anthropic, а затем запустить вашего бота.

## Отладка после деплоя

1. **Проверьте логи** в интерфейсе Railway для выявления ошибок
2. **Убедитесь**, что:
   - Бот действительно запущен (отправьте `/start` вашему боту)
   - В логах нет ошибок, связанных с proxies
   - API ключи правильно настроены
   
3. **Если появляются ошибки**, связанные с proxies:
   - Проверьте, что используется правильный import: `import anthropic_wrapper as anthropic`
   - Проверьте, что в `railway.json` указана правильная команда запуска
   - Убедитесь, что версия anthropic в `requirements.txt` равна 0.19.0
   
## Дополнительные ресурсы

- [Railway документация](https://docs.railway.app/)
- [Документация API Claude](https://docs.anthropic.com/claude/reference/)
- [Telegram Bot API](https://core.telegram.org/bots/api) 