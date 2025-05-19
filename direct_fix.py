#!/usr/bin/env python
"""
Прямое исправление проблемы с параметром proxies в Anthropic API.

Этот скрипт монкипатчит библиотеку anthropic на уровне создания клиента.
Обновлено для работы с новыми версиями библиотеки Anthropic.
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
    Применяет прямой патч к библиотеке Anthropic для исправления
    проблемы с параметром proxies.
    """
    try:
        # Импортируем библиотеку anthropic
        import anthropic
        from anthropic import Anthropic
        
        # Сохраняем оригинальный инициализатор
        original_init = Anthropic.__init__
        
        # Создаем новую версию инициализатора
        def patched_init(self, *args, **kwargs):
            # Логируем оригинальные параметры для отладки
            logger.info(f"Anthropic.__init__ вызван с kwargs: {kwargs}")
            
            # Удаляем проблемный параметр proxies
            if 'proxies' in kwargs:
                logger.info(f"[DIRECT FIX] Удаляем параметр proxies из Anthropic клиента")
                kwargs.pop('proxies')
                logger.info(f"kwargs после удаления proxies: {kwargs}")
            
            # Проверяем наличие других неподдерживаемых параметров
            valid_params = inspect.signature(original_init).parameters
            valid_param_names = set(valid_params.keys())
            unknown_params = set(kwargs.keys()) - valid_param_names
            
            for param in unknown_params:
                logger.info(f"[DIRECT FIX] Удаляем неизвестный параметр: {param}")
                kwargs.pop(param)
                
            # Вызываем оригинальный инициализатор с исправленными аргументами
            return original_init(self, *args, **kwargs)
        
        # Заменяем оригинальный метод на наш исправленный
        Anthropic.__init__ = patched_init
        
        # Выводим информацию об успешном патче
        logger.info("[DIRECT FIX] Клиент Anthropic успешно патчен")
        return True
    except Exception as e:
        logger.error(f"[DIRECT FIX] Ошибка при применении патча: {e}")
        return False

# Применяем патч
success = apply_direct_fix()
print(f"[DIRECT FIX] {'Успешно' if success else 'Не удалось'} применить прямой патч к Anthropic API")

# Модифицируем сам модуль anthropic для экспорта
try:
    # Делаем reimport модуля anthropic, чтобы он использовал наш патченый класс
    if "anthropic" in sys.modules:
        importlib.reload(sys.modules["anthropic"])
    
    # Экспортируем имена для использования в качестве модуля
    import anthropic
    Anthropic = anthropic.Anthropic
    
    # Функция для создания клиента без proxies
    def create_client(api_key=None):
        """
        Создает клиент Anthropic, безопасно удаляя параметр proxies.
        """
        import os
        if api_key is None:
            api_key = os.getenv("ANTHROPIC_API_KEY", "")
        
        logger.info(f"Создание клиента через патченый Anthropic")
        return Anthropic(api_key=api_key)
    
    # Дополнительный экспорт для совместимости
    from anthropic import *
    
    print("[DIRECT FIX] Модуль anthropic успешно модифицирован для экспорта")
except Exception as e:
    print(f"[DIRECT FIX] Ошибка при настройке экспорта: {e}")

# Опциональная проверка - попробуем создать клиент
try:
    import os
    
    # Получаем ключ API
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    
    if api_key:
        # Создаем клиент с тестовым proxies параметром
        client = anthropic.Anthropic(
            api_key=api_key,
            proxies={"http": None, "https": None}  # Этот параметр должен быть удален патчем
        )
        
        print("[DIRECT FIX] Тестовый клиент успешно создан!")
    else:
        print("[DIRECT FIX] API ключ не найден, тестирование пропущено")
except Exception as e:
    print(f"[DIRECT FIX] Ошибка при создании тестового клиента: {e}") 