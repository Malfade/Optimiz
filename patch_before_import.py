#!/usr/bin/env python
"""
Скрипт для патча библиотеки Anthropic непосредственно перед запуском бота.
Модифицирует исходный код модуля anthropic, чтобы он не использовал параметр proxies.
"""

import importlib
import sys
import logging
import os

# Настраиваем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("patch_anthropic")

def monkey_patch_anthropic():
    """
    Применяет патч к библиотеке anthropic, удаляя параметр proxies из аргументов __init__
    """
    try:
        # Импортируем модуль
        import anthropic
        
        # Запоминаем оригинальный метод
        original_init = anthropic.Anthropic.__init__
        
        # Определяем новый метод
        def patched_init(self, *args, **kwargs):
            # Удаляем параметр proxies из kwargs, если он присутствует
            if 'proxies' in kwargs:
                logger.info("PATCH: Удаляем параметр proxies из kwargs в конструкторе Anthropic")
                del kwargs['proxies']
            
            # Вызываем оригинальный метод
            return original_init(self, *args, **kwargs)
        
        # Подменяем метод
        anthropic.Anthropic.__init__ = patched_init
        
        logger.info("PATCH: Библиотека anthropic успешно модифицирована")
        return True
    except Exception as e:
        logger.error(f"PATCH: Ошибка при патче библиотеки anthropic: {e}")
        return False

# Применяем патч при импорте
success = monkey_patch_anthropic()
print(f"[PATCH ANTHROPIC] {'Успешно' if success else 'Не удалось'} применить патч к библиотеке anthropic")

# Модификация sys.modules для перезагрузки зависимых модулей
if success:
    # Находим и удаляем модули, которые могли уже загрузить библиотеку anthropic
    for module_name in list(sys.modules.keys()):
        if module_name == 'anthropic_helper' or 'optimization_bot' in module_name:
            logger.info(f"PATCH: Удаляем модуль {module_name} из sys.modules для перезагрузки")
            sys.modules.pop(module_name, None)
    
    print("[PATCH ANTHROPIC] Готово к запуску бота с патченой библиотекой") 