#!/usr/bin/env python
"""
Основной файл для запуска бота оптимизации Windows
Порядок импортов важен для работы в Railway!
"""
import os
import sys
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Проверка аргументов командной строки
if len(sys.argv) > 1 and sys.argv[1] == '--check-env':
    logger.info("Запрошена проверка окружения Railway")
    try:
        from check_railway_command import check_railway_env
        check_railway_env()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Ошибка при проверке окружения: {e}")
        sys.exit(1)

# КРИТИЧЕСКИ ВАЖНО: Очищаем переменные окружения прокси
# Railway автоматически добавляет эти переменные, что вызывает ошибки
proxy_env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
saved_proxies = {}

for env_var in proxy_env_vars:
    if env_var in os.environ:
        saved_proxies[env_var] = os.environ[env_var]
        logger.info(f"Удаляем переменную окружения {env_var}: {os.environ[env_var]}")
        del os.environ[env_var]

logger.info(f"Удалены переменные прокси: {saved_proxies}")

# Импортируем модуль проверки подписки
try:
    from subscription_check import check_user_subscription, add_user_subscription
    logger.info("✅ Модуль проверки подписки успешно загружен")
except Exception as e:
    logger.critical(f"❌ Ошибка при загрузке модуля подписки: {e}")
    sys.exit(1)

# Проверяем подписку перед запуском (используем ID из переменной окружения или значение по умолчанию)
BOT_OWNER_ID = os.getenv("BOT_OWNER_ID", "")
SUBSCRIPTION_CHECK_ENABLED = os.getenv("SUBSCRIPTION_CHECK_ENABLED", "true").lower() == "true"

# Функция проверки подписки
def check_subscription():
    # Если проверка подписки отключена в настройках, пропускаем проверку
    if not SUBSCRIPTION_CHECK_ENABLED:
        logger.info("Проверка подписки отключена в настройках, продолжаем запуск")
        return True
        
    # Если это Railway или другое облачное окружение, пропускаем проверку
    if os.getenv('RAILWAY_ENVIRONMENT') is not None:
        logger.info("Обнаружена среда Railway, пропускаем проверку подписки")
        return True
    
    # В тестовом режиме создаем временную подписку, если указан владелец бота
    if BOT_OWNER_ID:
        # Проверяем подписку владельца
        if check_user_subscription(BOT_OWNER_ID):
            logger.info(f"✅ Подписка активна для владельца бота (ID: {BOT_OWNER_ID})")
            return True
        else:
            # Создаем временную подписку для разработки
            add_user_subscription(BOT_OWNER_ID, "Тестовый план", 1, "dev_subscription")
            logger.warning(f"⚠️ Создана временная тестовая подписка для владельца (ID: {BOT_OWNER_ID})")
            return True
    
    # Для всех остальных случаев требуем наличие активной подписки
    logger.critical("❌ Активная подписка не найдена. Бот не может быть запущен.")
    return False

# Сначала импортируем fix_imports, который исправит импорты anthropic
try:
    import fix_imports
    logger.info("✅ Модуль fix_imports успешно загружен и применен")
except Exception as e:
    logger.critical(f"❌ Ошибка при загрузке fix_imports: {e}")
    sys.exit(1)

# Теперь anthropic должен быть доступен как fallback_anthropic
try:
    import anthropic
    logger.info(f"✅ Модуль anthropic успешно импортирован через fix_imports: {anthropic.__name__}")
    
    # Тестируем создание клиента
    test_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    logger.info(f"✅ Клиент успешно создан: {test_client.__class__.__name__}")
    
    # Тестовый запрос (опционально)
    try:
        if os.getenv("ANTHROPIC_API_KEY"):
            test_message = test_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Test connection"}]
            )
            logger.info(f"✅✅ ТЕСТОВЫЙ ЗАПРОС УСПЕШНО ОТПРАВЛЕН: {test_message.content[0].text[:20] if test_message.content else 'Нет ответа'}")
    except Exception as test_err:
        logger.warning(f"⚠️ Тестовый запрос не выполнен (некритично): {test_err}")
    
except Exception as e:
    logger.critical(f"❌❌❌ КРИТИЧЕСКАЯ ОШИБКА ПРИ ИНИЦИАЛИЗАЦИИ ANTHROPIC: {e}")
    sys.exit(1)

# Теперь импортируем основной файл бота
try:
    logger.info("🔄 Импортируем основной файл optimization_bot...")
    from optimization_bot import main
    logger.info("✅ Успешно импортирован основной файл optimization_bot")
except Exception as e:
    logger.critical(f"❌ Ошибка при импорте основного файла бота: {e}")
    sys.exit(1)

if __name__ == "__main__":
    logger.info("🚀 Запуск бота оптимизации Windows...")
    try:
        # Проверяем подписку перед запуском
        if check_subscription():
            main()
        else:
            # Если подписка не активна, выводим сообщение и завершаем работу
            print("❌ Для работы бота требуется активная подписка.")
            print("📱 Пожалуйста, откройте Telegram и оплатите подписку через мини-приложение.")
            sys.exit(1)
    except Exception as e:
        logger.critical(f"❌ Критическая ошибка при запуске бота: {e}")
        sys.exit(1)