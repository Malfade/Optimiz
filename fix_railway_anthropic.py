#!/usr/bin/env python
"""
Заглушка для обратной совместимости со старыми скриптами
Этот файл перенаправляет запуск на main.py
"""
import os
import sys
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("fix_railway_anthropic")

logger.info("⚠️ Внимание! Запущен устаревший скрипт fix_railway_anthropic.py.")
logger.info("Этот скрипт устарел и заменен на новую систему с использованием fix_imports.py")
logger.info("Перенаправляем выполнение на main.py...")

# Если файл запущен как основной скрипт, запускаем main.py
if __name__ == "__main__":
    try:
        # Пробуем импортировать main напрямую
        import main
        logger.info("✅ Файл main.py успешно импортирован")
        
        # Если main не содержит защиту if __name__ == "__main__"
        # мы должны вызвать его напрямую
        if hasattr(main, "main"):
            logger.info("📋 Запускаем main.main()")
            try:
                main.main()
            except Exception as e:
                logger.error(f"❌ Ошибка при выполнении main.main(): {e}")
                sys.exit(1)
        else:
            logger.info("✅ main.py выполнен при импорте")
    except ImportError:
        # Если импорт не работает, запускаем как отдельный процесс
        logger.warning("⚠️ Не удалось импортировать main.py, запускаем через os.system")
        exit_code = os.system("python main.py")
        
        if exit_code != 0:
            logger.error(f"❌ Ошибка при запуске main.py через os.system, код возврата: {exit_code}")
            sys.exit(exit_code)
        else:
            logger.info("✅ main.py успешно выполнен через os.system")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
        
    logger.info("✅ Работа завершена")
    sys.exit(0) 