# ✅ Чек-лист деплоя на Railway

Быстрый список действий для деплоя Optimizator Bot.

## 📋 Перед деплоем

### 🔑 Получите ключи:
- [ ] **Telegram Bot Token** от [@BotFather](https://t.me/BotFather)
- [ ] **Anthropic API Key** от [console.anthropic.com](https://console.anthropic.com/)
- [ ] **YooKassa Shop ID и Secret Key** от [yookassa.ru](https://yookassa.ru/)

### 📁 Проверьте файлы:
- [ ] `optimization_bot.py` - основной файл бота
- [ ] `templates/payment.html` - HTML интерфейса
- [ ] `static/payment.css` - стили
- [ ] `static/payment.js` - JavaScript
- [ ] `requirements.txt` - зависимости
- [ ] `railway.json` - конфигурация Railway

## 🚀 Деплой на Railway

### 1. Создание проекта:
- [ ] Зайти на [railway.app](https://railway.app/)
- [ ] Нажать "Start a New Project"
- [ ] Выбрать "Deploy from GitHub repo"
- [ ] Подключить репозиторий

### 2. Настройка переменных:
Добавить в **Variables**:

**Обязательные:**
- [ ] `TELEGRAM_TOKEN=ваш_токен`
- [ ] `ANTHROPIC_API_KEY=ваш_ключ`
- [ ] `PAYMENT_SYSTEM_URL=https://ваш-проект.up.railway.app`

**Платежи:**
- [ ] `YOOKASSA_SHOP_ID=ваш_shop_id`
- [ ] `YOOKASSA_SECRET_KEY=ваш_secret_key`
- [ ] `TEST_MODE=true`
- [ ] `WEBHOOK_SECRET=случайная_строка`

**Системные:**
- [ ] `PORT=5000`
- [ ] `ENABLE_SUBSCRIPTIONS=true`
- [ ] `RAILWAY_ENVIRONMENT=production`
- [ ] `DEBUG=false`
- [ ] `LOG_LEVEL=INFO`

### 3. Получение URL:
- [ ] Дождаться завершения деплоя
- [ ] Скопировать URL в **Settings** → **Domains**
- [ ] Обновить `PAYMENT_SYSTEM_URL` на полученный URL

## 🤖 Настройка бота

### Мини-приложение в @BotFather:
- [ ] Открыть [@BotFather](https://t.me/BotFather)
- [ ] `/mybots` → выбрать бота
- [ ] **Bot Settings** → **Menu Button**
- [ ] Указать:
  - Button text: `💳 Подписка`
  - Web App URL: `https://ваш-проект.up.railway.app`

### Команды бота (опционально):
- [ ] Отправить `/setcommands` в @BotFather
- [ ] Добавить список команд:
```
start - Запустить бота
help - Помощь по использованию
stats - Статистика скриптов
subscription - Информация о подписке
cancel - Отменить текущую операцию
```

## 💰 Настройка YooKassa

### Webhook для продакшена:
- [ ] В панели YooKassa → **Webhook URL**
- [ ] Указать: `https://ваш-проект.up.railway.app/api/webhook`
- [ ] Выбрать события: `payment.succeeded`, `payment.canceled`

## ✅ Тестирование

### Основные проверки:
- [ ] Открыть `https://ваш-проект.up.railway.app` - должен загрузиться интерфейс
- [ ] Отправить `/start` боту - должны появиться кнопки
- [ ] Попробовать создать скрипт - должна появиться кнопка подписки
- [ ] Нажать кнопку подписки - должно открыться мини-приложение

### Проверка логов в Railway:
Должны появиться сообщения:
- [ ] ✅ "Веб-сервер запущен в отдельном потоке"
- [ ] ✅ "Соединение с Telegram API установлено успешно"
- [ ] ✅ "Healthcheck сервер успешно запущен"

## 🚨 Если что-то не работает

### Быстрая диагностика:
1. **Бот не отвечает** → Проверить `TELEGRAM_TOKEN`
2. **Мини-приложение не открывается** → Проверить URL в @BotFather
3. **Платежи не работают** → Проверить ключи YooKassa
4. **Ошибки деплоя** → Проверить логи в Railway

### Где искать логи:
- Railway: **Deployments** → выбрать последний деплой
- Telegram: отправить `/help` боту для проверки работы

---

## 🎯 Готово!

После выполнения всех пунктов ваш бот готов к работе! 

Для подробной информации см. [RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md) 