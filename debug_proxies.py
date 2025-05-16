#!/usr/bin/env python
"""
Скрипт для диагностики проблемы с параметром proxies в библиотеке anthropic.
Переопределяет ключевые функции для отслеживания вызовов.
"""

import os
import sys
import inspect
import logging
import traceback

# Настройка логирования в файл и консоль
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug_proxies.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("debug_proxies")

def debug_import_hook():
    """Устанавливает хук на все импорты для отслеживания"""
    original_import = __builtins__.__import__
    
    def custom_import(name, *args, **kwargs):
        module = original_import(name, *args, **kwargs)
        if name == 'anthropic':
            logger.info(f"Модуль anthropic импортирован из {module.__file__}")
            
            # Патчим класс Anthropic
            if hasattr(module, 'Anthropic'):
                original_init = module.Anthropic.__init__
                
                def debug_init(self, *args, **kwargs):
                    logger.info(f"Anthropic.__init__ вызван с аргументами: {args}")
                    logger.info(f"Anthropic.__init__ вызван с ключевыми аргументами: {list(kwargs.keys())}")
                    
                    # Получаем стек вызовов
                    stack = traceback.extract_stack()
                    caller_info = stack[-2]  # Вызывающая функция
                    logger.info(f"Вызов из: {caller_info.filename}:{caller_info.lineno}")
                    
                    # Удаляем proxies
                    if 'proxies' in kwargs:
                        logger.info(f"Обнаружен proxies: {kwargs['proxies']}")
                        del kwargs['proxies']
                        logger.info("Параметр proxies удален")
                    
                    # Вызываем оригинальный метод
                    return original_init(self, *args, **kwargs)
                
                # Устанавливаем патч
                module.Anthropic.__init__ = debug_init
                logger.info("Класс Anthropic успешно патчен")
        
        return module
    
    # Заменяем встроенную функцию импорта
    __builtins__.__import__ = custom_import
    logger.info("Установлен хук для отслеживания импортов")

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Запуск диагностики проблемы с параметром proxies")
    logger.info("=" * 60)
    
    # Установка хуков для отслеживания
    debug_import_hook()
    
    # Печать текущего окружения
    logger.info(f"Python: {sys.version}")
    logger.info(f"Рабочая директория: {os.getcwd()}")
    
    # Проверка установленных пакетов
    try:
        import pkg_resources
        for dist in pkg_resources.working_set:
            if 'anthropic' in dist.project_name:
                logger.info(f"Установлен пакет: {dist.project_name}=={dist.version}")
    except Exception as e:
        logger.error(f"Ошибка при проверке пакетов: {e}")
    
    logger.info("Диагностика завершена")
    print("[DEBUG] Установлены хуки для отслеживания проблемы с proxies. См. файл debug_proxies.log") 