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

# Очищаем переменные окружения прокси
# Railway автоматически добавляет эти переменные, что вызывает ошибки
for env_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    if env_var in os.environ:
        logger.info(f"Удаляем переменную окружения {env_var}")
        del os.environ[env_var]

# Применяем патч для Railway перед импортом anthropic
if os.environ.get('RAILWAY_ENVIRONMENT') is not None:
    logger.info("Обнаружена среда Railway, применяем патч для anthropic")
    try:
        # Сначала загружаем патч для решения проблемы с proxies
        import fix_railway_anthropic
        logger.info("Патч для Railway успешно загружен")
    except Exception as e:
        logger.error(f"Ошибка при загрузке патча для Railway: {e}")

# Пытаемся импортировать anthropic с несколькими резервными вариантами
anthropic = None
import_errors = []

# Попытка 1: Используем нашу самую надежную резервную реализацию
try:
    logger.info("Пытаемся использовать fallback_anthropic")
    import fallback_anthropic as anthropic
    logger.info("✅ Импортирована резервная версия fallback_anthropic")
    # Проверим, действительно ли она работает
    test_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    logger.info("✅ Тестовый клиент fallback_anthropic успешно создан!")
except Exception as e:
    import_errors.append(f"Ошибка fallback_anthropic: {e}")
    logger.warning(f"Не удалось использовать fallback_anthropic: {e}")
    anthropic = None

# Попытка 2: Используем безопасную обертку
if anthropic is None:
    try:
        logger.info("Пытаемся использовать safe_anthropic")
        import safe_anthropic as anthropic
        logger.info("✅ Импортирована безопасная версия safe_anthropic")
        # Проверим, действительно ли она работает
        test_client = anthropic.create_client(api_key=os.getenv("ANTHROPIC_API_KEY"))
        logger.info("✅ Тестовый клиент safe_anthropic успешно создан!")
    except Exception as e:
        import_errors.append(f"Ошибка safe_anthropic: {e}")
        logger.warning(f"Не удалось использовать safe_anthropic: {e}")
        anthropic = None

# Попытка 3: Используем другую обертку
if anthropic is None:
    try:
        logger.info("Пытаемся использовать anthropic_wrapper")
        import anthropic_wrapper as anthropic
        logger.info("✅ Импортирована обертка anthropic_wrapper")
        # Проверим, действительно ли она работает
        if hasattr(anthropic, 'create_client'):
            test_client = anthropic.create_client(api_key=os.getenv("ANTHROPIC_API_KEY"))
        else:
            test_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        logger.info("✅ Тестовый клиент anthropic_wrapper успешно создан!")
    except Exception as e:
        import_errors.append(f"Ошибка anthropic_wrapper: {e}")
        logger.warning(f"Не удалось использовать anthropic_wrapper: {e}")
        anthropic = None

# Попытка 4: Используем оригинальную библиотеку как последнее средство
if anthropic is None:
    try:
        logger.info("Пытаемся использовать оригинальную библиотеку anthropic")
        import anthropic
        logger.info("✅ Импортирована оригинальная библиотека anthropic")
        # Проверим, действительно ли она работает
        test_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        logger.info("✅ Тестовый клиент оригинальной библиотеки успешно создан!")
    except Exception as e:
        import_errors.append(f"Ошибка оригинального anthropic: {e}")
        logger.warning(f"Не удалось использовать оригинальную библиотеку anthropic: {e}")
        anthropic = None

# Проверяем, импортировали ли мы хоть какую-то версию anthropic
if anthropic is None:
    error_msg = "Не удалось импортировать ни одну из версий anthropic. Ошибки:\n" + "\n".join(import_errors)
    logger.critical(error_msg)
    sys.exit(1)
else:
    logger.info(f"Успешно импортирован: {anthropic.__name__}, версия: {getattr(anthropic, '__version__', 'unknown')}")

# Сообщаем системе, что мы будем использовать эту версию anthropic
sys.modules['anthropic'] = anthropic

# Теперь импортируем основной файл бота
try:
    from optimization_bot import main
    logger.info("Успешно импортирован основной файл optimization_bot")
except Exception as e:
    logger.critical(f"Ошибка при импорте основного файла бота: {e}")
    sys.exit(1)

if __name__ == "__main__":
    logger.info("Запуск бота оптимизации Windows...")
    try:
        main()
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")
        sys.exit(1) 