# Optimizator Bot - Бот для оптимизации Windows

Telegram бот с интегрированной платежной системой для создания скриптов оптимизации Windows.

## 🚀 Быстрый деплой на Railway

### 📁 Что нужно для деплоя:
```
optimizator/
├── optimization_bot.py      # ✅ Основной файл (бот + веб-сервер)
├── templates/payment.html   # ✅ HTML мини-приложения
├── static/payment.css       # ✅ Стили интерфейса
├── static/payment.js        # ✅ JavaScript логика
├── requirements.txt         # ✅ Зависимости Python
├── railway.json            # ✅ Конфигурация Railway
├── example.env             # ✅ Пример настроек
├── RAILWAY_DEPLOY.md       # 📖 Подробная инструкция
└── DEPLOY_CHECKLIST.md     # ✅ Быстрый чек-лист
```

### 🔑 Нужные ключи:
- **Telegram Bot Token** - от [@BotFather](https://t.me/BotFather)
- **Anthropic API Key** - от [console.anthropic.com](https://console.anthropic.com/)
- **YooKassa данные** - от [yookassa.ru](https://yookassa.ru/)

### ⚡ Деплой за 5 минут:
1. **Форкните репозиторий** на GitHub
2. **Подключите к Railway** ([railway.app](https://railway.app/))
3. **Добавьте переменные** (см. [DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md))
4. **Настройте мини-приложение** в @BotFather
5. **Готово!** 🎉

## 💡 Возможности

- 🔧 **Создание скриптов оптимизации** на основе скриншотов системы
- 🔨 **Исправление ошибок** в скриптах через AI
- 💳 **Интегрированная платежная система** с ЮKassa
- 📱 **Мини-приложение** для управления подписками
- 🛡️ **Система подписок** с проверкой доступа

## 📖 Документация

- **[DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md)** - ✅ Быстрый чек-лист для деплоя
- **[RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md)** - 📖 Подробная инструкция
- **[example.env](example.env)** - ⚙️ Пример переменных окружения
- **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** - 🔧 Техническая интеграция

## 🔧 Локальная разработка

```bash
# 1. Клонируйте репозиторий
git clone <repository-url>
cd optimizator

# 2. Установите зависимости
pip install -r requirements.txt

# 3. Настройте переменные
cp example.env .env
# Отредактируйте .env с вашими ключами

# 4. Запустите бота
python optimization_bot.py
```

## 🆘 Поддержка

**Проблемы при деплое?**
1. Проверьте [DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md)
2. Изучите [RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md)
3. Проверьте логи в Railway
4. Обратитесь с логами ошибок

**Популярные проблемы:**
- Бот не отвечает → Проверьте `TELEGRAM_TOKEN`
- Мини-приложение не открывается → Проверьте URL в @BotFather
- Платежи не работают → Проверьте ключи YooKassa

## 🏗️ Архитектура

**Единый проект включает:**
- **Telegram Bot** (pyTelegramBotAPI)
- **Веб-сервер Flask** для мини-приложения
- **Платежная система** (YooKassa)
- **AI генерация** скриптов (Anthropic Claude)
- **Система подписок**

**Преимущества единого проекта:**
- ✅ Один деплой вместо двух
- ✅ Общие переменные окружения
- ✅ Единые логи и мониторинг
- ✅ Меньше затрат на хостинге

---

🎯 **Готов к деплою на Railway за 5 минут!** Следуйте [DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md)

## Лицензия

MIT License
