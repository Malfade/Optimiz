#!/usr/bin/env python
"""
Патч для исправления проблемы с параметром proxies в библиотеке Anthropic.
Этот файл монкипатчит библиотеку, чтобы избежать ошибки с параметром proxies.
"""

import os
import sys
import logging
import importlib
import anthropic

logger = logging.getLogger("override_anthropic")

def patch_anthropic():
    """
    Монкипатчит класс Anthropic, переопределяя его __init__ метод
    для удаления любых неподдерживаемых аргументов, включая proxies.
    """
    # Сохраняем оригинальный метод
    original_init = anthropic.Anthropic.__init__
    
    # Определяем новый метод с обработкой лишних параметров
    def safe_init(self, *args, **kwargs):
        """Безопасная версия __init__, которая удаляет proxies и другие проблемные параметры"""
        # Удаляем нежелательные параметры
        if 'proxies' in kwargs:
            logger.info("Удаляем параметр proxies из инициализации Anthropic клиента")
            del kwargs['proxies']
        
        # Вызываем оригинальный инициализатор с очищенными параметрами
        return original_init(self, *args, **kwargs)
    
    # Применяем патч
    anthropic.Anthropic.__init__ = safe_init
    logger.info("Класс Anthropic успешно патчен для обхода проблемы с proxies")
    
    return True

# Применяем патч при импорте модуля
patch_successful = patch_anthropic()
print(f"✅ Monkey patching для Anthropic API выполнен {'успешно' if patch_successful else 'с ошибкой'}") 