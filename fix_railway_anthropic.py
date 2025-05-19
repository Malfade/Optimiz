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

def patch_anthropic():
    """
    Патчит модуль anthropic для предотвращения ошибки с proxies
    """
    logger.info("Применяю глобальный патч для anthropic в Railway")
    
    # Проверяем, не находимся ли мы в Railway
    if os.environ.get('RAILWAY_ENVIRONMENT') is None:
        logger.info("Не обнаружена среда Railway, патч не требуется")
        return True
    
    try:
        # 1. Прямой monkey-patch стандартной библиотеки httpx
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
        except ImportError:
            logger.warning("Модуль httpx не найден, этот этап патча пропущен")
        
        # 2. Проверяем, импортирован ли уже модуль anthropic
        if 'anthropic' in sys.modules:
            logger.warning("Модуль anthropic уже импортирован! Патч может быть неэффективным!")
        
        # 3. Предварительный патч для anthropic
        import importlib.util
        spec = importlib.util.find_spec('anthropic')
        if spec is None:
            logger.error("Модуль anthropic не установлен")
            return False
        
        module = importlib.util.module_from_spec(spec)
        
        # Сохраняем оригинальный exec_module
        original_exec_module = spec.loader.exec_module
        
        def patched_exec_module(mod):
            # Запускаем оригинальный код загрузки модуля
            original_exec_module(mod)
            
            # После загрузки модуля патчим его методы
            if hasattr(mod, 'Anthropic'):
                logger.info("Патчим модуль anthropic.Anthropic.__init__")
                
                original_init = mod.Anthropic.__init__
                
                def patched_init(self, *args, **kwargs):
                    # Обрабатываем параметр proxies
                    if 'proxies' in kwargs:
                        logger.info(f"Преобразуем формат proxies в Anthropic.__init__: {kwargs['proxies']}")
                        # Преобразуем в правильный формат и удаляем, если они None
                        proxies = convert_proxy_format(kwargs['proxies'])
                        if proxies is None or all(v is None for v in proxies.values()):
                            logger.info("Удаляем параметр proxies, так как все значения None")
                            del kwargs['proxies']
                        else:
                            kwargs['proxies'] = proxies
                    
                    # Поскольку в разных версиях anthropic разные параметры, проверяем сигнатуру
                    sig = inspect.signature(original_init)
                    valid_params = set(sig.parameters.keys())
                    filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_params or k == 'self'}
                    
                    logger.info(f"Вызываем оригинальный Anthropic.__init__ с очищенными аргументами")
                    return original_init(self, *args, **filtered_kwargs)
                
                # Применяем патч
                mod.Anthropic.__init__ = patched_init
            
            # Патчим Client, если он существует
            if hasattr(mod, 'Client'):
                logger.info("Патчим модуль anthropic.Client.__init__")
                
                original_client_init = mod.Client.__init__
                
                def patched_client_init(self, *args, **kwargs):
                    # Обрабатываем параметр proxies
                    if 'proxies' in kwargs:
                        logger.info(f"Преобразуем формат proxies в Client.__init__: {kwargs['proxies']}")
                        # Преобразуем в правильный формат и удаляем, если они None
                        proxies = convert_proxy_format(kwargs['proxies'])
                        if proxies is None or all(v is None for v in proxies.values()):
                            logger.info("Удаляем параметр proxies, так как все значения None")
                            del kwargs['proxies']
                        else:
                            kwargs['proxies'] = proxies
                    
                    # Фильтруем параметры по сигнатуре
                    sig = inspect.signature(original_client_init)
                    valid_params = set(sig.parameters.keys())
                    filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_params or k == 'self'}
                    
                    return original_client_init(self, *args, **filtered_kwargs)
                
                # Применяем патч
                mod.Client.__init__ = patched_client_init
            
            return mod
        
        # Заменяем метод загрузки модуля на наш патченый
        spec.loader.exec_module = lambda mod: patched_exec_module(mod)
        
        # Заносим модуль в sys.modules
        sys.modules['anthropic'] = module
        
        logger.info("Патч для модуля anthropic успешно применен")
        
        # Создаем функцию для тестирования
        def test_anthropic():
            try:
                from anthropic import Anthropic
                # Используем правильный формат URL для прокси
                client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", "test_key"), 
                                   proxies={"http://": None, "https://": None})
                logger.info("✅ Тест успешен: создан клиент Anthropic с параметром proxies без ошибок")
                return True
            except Exception as e:
                logger.error(f"❌ Тест не пройден: {e}")
                return False
        
        # Выполняем тест
        test_result = test_anthropic()
        
        return test_result
    
    except Exception as e:
        logger.error(f"Ошибка при патче модуля anthropic: {e}")
        return False

if __name__ == "__main__":
    success = patch_anthropic()
    if success:
        print("[RAILWAY ANTHROPIC PATCH] Успешно применен патч для решения проблемы с proxies!")
    else:
        print("[RAILWAY ANTHROPIC PATCH] Ошибка при применении патча!")
    
    # Добавляем пустую строку для разделения вывода
    print("") 