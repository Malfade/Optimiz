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

# Применяем патч для Railway перед импортом anthropic
if os.environ.get('RAILWAY_ENVIRONMENT') is not None:
    logger.info("Обнаружена среда Railway, применяем патч для anthropic")
    try:
        # Сначала загружаем патч для решения проблемы с proxies
        import fix_railway_anthropic
        logger.info("Патч для Railway успешно загружен")
    except Exception as e:
        logger.error(f"Ошибка при загрузке патча для Railway: {e}")

# Затем импортируем безопасную версию anthropic
try:
    # Пробуем использовать безопасную обертку
    import safe_anthropic as anthropic
    logger.info("Импортирована безопасная версия anthropic")
except ImportError:
    try:
        # Запасной вариант - использовать другую обертку
        import anthropic_wrapper as anthropic
        logger.info("Импортирована обертка anthropic_wrapper")
    except ImportError:
        # Если не удалось, используем оригинальную библиотеку
        logger.warning("Не удалось импортировать безопасные обертки, используем оригинальную библиотеку")
        import anthropic

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