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

# ИСПОЛЬЗУЕМ ТОЛЬКО FALLBACK РЕАЛИЗАЦИЮ
# Игнорируем все другие варианты (safe_anthropic, anthropic_wrapper и оригинальную библиотеку)
try:
    logger.info("▶️ ИСПОЛЬЗУЕМ ТОЛЬКО FALLBACK_ANTHROPIC - САМЫЙ НАДЕЖНЫЙ ВАРИАНТ")
    
    # Подменяем модуль anthropic на наш fallback_anthropic
    import fallback_anthropic
    sys.modules['anthropic'] = fallback_anthropic
    import anthropic
    
    # Проверим, действительно ли работает
    logger.info("🔍 Проверяем работоспособность fallback_anthropic...")
    test_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    logger.info(f"✅ Клиент успешно создан! {test_client.__class__.__name__}")
    
    # Вторая проверка
    try:
        test_message = test_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hello!"}]
        )
        logger.info(f"✅✅ ТЕСТОВОЕ СООБЩЕНИЕ УСПЕШНО ОТПРАВЛЕНО! {test_message.content[0].text[:20] if test_message.content else 'Нет контента'}")
    except Exception as msg_error:
        logger.error(f"❌ Ошибка при отправке тестового сообщения: {msg_error}")
    
    logger.info("✅✅✅ FALLBACK ANTHROPIC УСПЕШНО ИНИЦИАЛИЗИРОВАН")
except Exception as e:
    logger.critical(f"❌❌❌ КРИТИЧЕСКАЯ ОШИБКА ПРИ ИНИЦИАЛИЗАЦИИ FALLBACK_ANTHROPIC: {e}")
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