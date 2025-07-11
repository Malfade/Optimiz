# Система оплаты за скрипты

## Описание

Система позволяет пользователям покупать пакеты скриптов оптимизации вместо ежемесячных подписок.

## Доступные пакеты

1. **1 скрипт** - 49₽
   - Создание одного скрипта оптимизации
   - Срок действия: 30 дней

2. **3 скрипта** - 129₽ (экономия 15%)
   - 3 скрипта оптимизации
   - Срок действия: 30 дней
   - Популярный выбор

3. **10 скриптов** - 399₽ (экономия 20%)
   - 10 скриптов оптимизации
   - Срок действия: 30 дней
   - Максимальная выгода

## Как работает

1. Пользователь отправляет скриншот системы
2. Бот проверяет наличие доступных скриптов
3. Если скриптов нет - показывает кнопку покупки
4. После покупки пользователь может создавать скрипты
5. После каждого созданного скрипта счетчик уменьшается

## Тестовый режим

- Используется тестовая YooKassa (shop_id: 1086529)
- Реальные деньги не списываются
- Все платежи проходят в тестовом режиме

## Команды бота

- `/start` - Запуск бота
- `/subscription` - Проверка оставшихся скриптов
- `/help` - Помощь
- `/cancel` - Отмена текущего действия

## Настройка

1. Скопируйте `example.env` в `.env`
2. Заполните необходимые переменные:
   - `TELEGRAM_TOKEN` - токен вашего бота
   - `ANTHROPIC_API_KEY` - API ключ Claude
   - `PAYMENT_SYSTEM_URL` - URL вашего приложения на Railway

## Деплой на Railway

1. Подключите репозиторий к Railway
2. Установите переменные окружения из `.env`
3. Railway автоматически развернет приложение
4. Получите URL и обновите `PAYMENT_SYSTEM_URL`

## Файлы системы

- `optimization_bot.py` - основной бот
- `subscription_check.py` - система подписок и генераций
- `payment_system/` - веб-интерфейс для оплаты
- `example.env` - пример переменных окружения 