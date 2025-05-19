#!/usr/bin/env python
"""
Прямое исправление проблемы с параметром proxies в Anthropic API.

Этот скрипт монкипатчит библиотеку anthropic на самом базовом уровне,
изменяя код инициализации базового HTTP клиента, который принимает параметр proxies.
"""

import sys
import logging
import inspect
import importlib

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("direct_fix")

def apply_direct_fix():
    """
    Применяет прямой патч к базовому HTTP клиенту Anthropic для исправления
    проблемы с параметром proxies.
    """
    try:
        # Импортируем базовый класс из anthropic
        import anthropic
        from anthropic._base_client import SyncHttpxClientWrapper
        
        # Сохраняем оригинальный инициализатор
        original_init = SyncHttpxClientWrapper.__init__
        
        # Создаем новую версию инициализатора
        def patched_init(self, *args, **kwargs):
            # Удаляем проблемный параметр proxies
            if 'proxies' in kwargs:
                logger.info(f"[DIRECT FIX] Удаляем параметр proxies из базового HTTP клиента")
                del kwargs['proxies']
                
            # Вызываем оригинальный инициализатор с исправленными аргументами
            return original_init(self, *args, **kwargs)
        
        # Заменяем оригинальный метод на наш исправленный
        SyncHttpxClientWrapper.__init__ = patched_init
        
        # Проверяем сигнатуру функции с patched_init
        logger.info(f"Сигнатура патченого инициализатора: {inspect.signature(SyncHttpxClientWrapper.__init__)}")
        
        # Выводим информацию об успешном патче
        logger.info("[DIRECT FIX] Базовый HTTP клиент Anthropic успешно патчен")
        return True
    except Exception as e:
        logger.error(f"[DIRECT FIX] Ошибка при применении патча: {e}")
        return False

# Применяем патч
success = apply_direct_fix()
print(f"[DIRECT FIX] {'Успешно' if success else 'Не удалось'} применить прямой патч к Anthropic API")

# Опциональная проверка - попробуем создать клиент
try:
    import os
    import anthropic
    
    # Получаем ключ API
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Создаем клиент с тестовым proxies параметром
    client = anthropic.Anthropic(
        api_key=api_key,
        proxies={"http": None, "https": None}  # Этот параметр должен быть удален патчем
    )
    
    print("[DIRECT FIX] Тестовый клиент успешно создан!")
except Exception as e:
    print(f"[DIRECT FIX] Ошибка при создании тестового клиента: {e}") 