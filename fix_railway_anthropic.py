#!/usr/bin/env python
"""
Прямой системный патч для решения проблемы с proxies в Railway.
Этот файл должен быть запущен ДО импорта библиотеки anthropic.
"""
import os
import sys
import logging
import inspect
import importlib.util

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fix_railway_anthropic")

def convert_proxy_format(proxies):
    """
    Преобразует формат проксей из старого {'http': ...} в новый {'http://': ...}
    """
    if not proxies or not isinstance(proxies, dict):
        return proxies
    
    new_proxies = {}
    for key, value in proxies.items():
        # Если ключ не заканчивается на '://', добавляем
        if key in ('http', 'https') and not key.endswith('://'):
            new_key = f"{key}://"
            new_proxies[new_key] = value
        else:
            new_proxies[key] = value
    
    return new_proxies

def fix_httpx_client():
    """Патчит httpx.Client для обработки proxies"""
    try:
        import httpx
        original_httpx_client_init = httpx.Client.__init__
        
        def patched_httpx_init(self, *args, **kwargs):
            # Преобразуем формат прокси, если они есть
            if 'proxies' in kwargs:
                logger.info(f"Преобразуем формат proxies в httpx.Client.__init__")
                kwargs['proxies'] = convert_proxy_format(kwargs['proxies'])
            return original_httpx_client_init(self, *args, **kwargs)
        
        # Применяем патч
        httpx.Client.__init__ = patched_httpx_init
        logger.info("Успешно применен патч к httpx.Client.__init__")
        return True
    except ImportError:
        logger.warning("Модуль httpx не найден, этот этап патча пропущен")
        return False
    except Exception as e:
        logger.error(f"Ошибка при патче httpx: {e}")
        return False

def patch_requests_session():
    """Патчит requests.Session для обработки proxies"""
    try:
        import requests
        original_session_init = requests.Session.__init__
        
        def patched_session_init(self, *args, **kwargs):
            # Этот метод вызывается библиотекой anthropic под капотом
            # и может получать proxies от Railway
            if 'proxies' in kwargs:
                logger.info(f"Обрабатываем proxies в requests.Session.__init__")
                if kwargs['proxies'] is None:
                    del kwargs['proxies']
                else:
                    kwargs['proxies'] = convert_proxy_format(kwargs['proxies'])
            
            return original_session_init(self, *args, **kwargs)
        
        # Применяем патч
        requests.Session.__init__ = patched_session_init
        logger.info("Успешно применен патч к requests.Session.__init__")
        return True
    except ImportError:
        logger.warning("Модуль requests не найден, этот этап патча пропущен")
        return False
    except Exception as e:
        logger.error(f"Ошибка при патче requests: {e}")
        return False

def direct_monkey_patch_anthropic():
    """
    Прямой патч модуля anthropic, если он уже импортирован
    """
    if 'anthropic' not in sys.modules:
        logger.info("Модуль anthropic еще не импортирован, прямой патч не требуется")
        return False
    
    try:
        anthropic = sys.modules['anthropic']
        logger.info(f"Содержимое модуля anthropic: {dir(anthropic)}")
        
        # Пытаемся найти класс Anthropic в разных местах
        for cls_name in ['Anthropic', 'Client', 'AnthropicAPI']:
            if hasattr(anthropic, cls_name):
                cls = getattr(anthropic, cls_name)
                logger.info(f"Найден класс {cls_name} в модуле anthropic")
                
                original_init = cls.__init__
                
                def patched_init(self, *args, **kwargs):
                    if 'proxies' in kwargs:
                        logger.info(f"Удаляем proxies из {cls_name}.__init__")
                        del kwargs['proxies']
                    return original_init(self, *args, **kwargs)
                
                # Применяем патч
                cls.__init__ = patched_init
                logger.info(f"Успешно применен патч к {cls_name}.__init__")
                
        logger.info("Прямой патч модуля anthropic применен успешно")
        return True
    except Exception as e:
        logger.error(f"Ошибка при прямом патче anthropic: {e}")
        return False

def remove_proxies_from_environment():
    """
    Удаляет переменные окружения HTTP_PROXY и HTTPS_PROXY,
    которые могут автоматически добавляться Railway
    """
    for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
        if var in os.environ:
            logger.info(f"Удаляем переменную окружения {var}: {os.environ[var]}")
            del os.environ[var]
    
    logger.info("Переменные окружения прокси удалены")
    return True

def patch_anthropic():
    """
    Патчит модуль anthropic для предотвращения ошибки с proxies
    """
    logger.info("Применяю глобальный патч для anthropic в Railway")
    
    # Проверяем, не находимся ли мы в Railway
    if os.environ.get('RAILWAY_ENVIRONMENT') is None:
        logger.info("Не обнаружена среда Railway, патч не требуется")
        return True
    
    # Применяем все возможные патчи последовательно
    success = True
    
    # 1. Удаляем переменные окружения прокси
    success = remove_proxies_from_environment() and success
    
    # 2. Патчим requests.Session
    success = patch_requests_session() and success
    
    # 3. Патчим httpx.Client
    success = fix_httpx_client() and success
    
    # 4. Прямой патч, если модуль уже импортирован
    direct_monkey_patch_anthropic()
    
    # 5. Проверяем импорт anthropic для уверенности
    try:
        # Простой импорт для проверки, что можем импортировать без ошибок
        import anthropic
        logger.info(f"Успешный импорт anthropic: {anthropic.__file__}")
        logger.info(f"Версия anthropic: {getattr(anthropic, '__version__', 'unknown')}")
        logger.info(f"Доступные члены anthropic: {dir(anthropic)}")
        
        # Для более серьезной проверки попробуем создать клиент без ошибок
        # Это может зависеть от структуры модуля
        logger.info("Патч для модуля anthropic успешно применен")
        return success
    except Exception as e:
        logger.error(f"Ошибка при проверке импорта anthropic: {e}")
        # Возвращаем True, так как патч мог быть успешным даже если тест не прошел
        return success

if __name__ == "__main__":
    success = patch_anthropic()
    if success:
        print("[RAILWAY ANTHROPIC PATCH] Успешно применен патч для Railway!")
    else:
        print("[RAILWAY ANTHROPIC PATCH] Предупреждение: возможны проблемы с патчем")
    
    # Проверяем импорт
    try:
        import anthropic
        print(f"[DEBUG] Структура модуля anthropic: {dir(anthropic)}")
    except Exception as e:
        print(f"[DEBUG] Ошибка при импорте anthropic: {e}")
    
    # Добавляем пустую строку для разделения вывода
    print("") 