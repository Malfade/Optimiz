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
        main()
    except Exception as e:
        logger.critical(f"❌ Критическая ошибка при запуске бота: {e}")
        sys.exit(1)