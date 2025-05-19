#!/usr/bin/env python
"""
Обертка для Anthropic API, которая гарантирует, что параметр 'proxies' не будет передан.
Этот скрипт нужно импортировать и использовать вместо прямого импорта библиотеки anthropic.

Адаптирован для работы с версией 0.19.0, где параметр proxies присутствует в сигнатуре,
но вызывает ошибку при использовании.
"""

import os
import logging
import importlib
import sys
import inspect

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("anthropic_wrapper")

# Определение переменных для экспорта
Client = None
Anthropic = None

# Попытка импорта безопасной версии
try:
    # Импортируем safe_anthropic, если доступен
    try:
        import safe_anthropic
        logger.info("Импортирован безопасный модуль safe_anthropic")
        
        # Экспортируем основные классы и функции
        Anthropic = safe_anthropic.Anthropic
        Client = safe_anthropic.Client if hasattr(safe_anthropic, 'Client') else None
        create_client = safe_anthropic.create_client if hasattr(safe_anthropic, 'create_client') else None
        
        # Экспортируем все другие компоненты
        for name in dir(safe_anthropic):
            if not name.startswith('_') and name not in globals():
                globals()[name] = getattr(safe_anthropic, name)
        
    except ImportError:
        # Если safe_anthropic недоступен, создаем свою обертку
        logger.info("Модуль safe_anthropic недоступен, создаем собственную обертку")
        
        # Импортируем оригинальную библиотеку
        import anthropic as original_anthropic
        
        # Создаем безопасную версию Anthropic
        class SafeAnthropicWrapper(original_anthropic.Anthropic):
            """
            Безопасная обертка для Anthropic, которая удаляет параметр proxies
            и другие неподдерживаемые параметры.
            """
            def __init__(self, *args, **kwargs):
                logger.info(f"SafeAnthropicWrapper: Инициализация с kwargs: {kwargs}")
                
                # Удаляем параметр proxies, если он присутствует
                proxies_value = None
                if 'proxies' in kwargs:
                    logger.info(f"SafeAnthropicWrapper: Удаляем параметр proxies: {kwargs['proxies']}")
                    proxies_value = kwargs.pop('proxies')
                
                # Получаем сигнатуру родительского метода
                orig_sig = inspect.signature(original_anthropic.Anthropic.__init__)
                valid_params = set(orig_sig.parameters.keys())
                
                # Удаляем все параметры, которых нет в сигнатуре или которые вызывают ошибки
                known_problematic_params = {'proxies'}  # параметры, которые есть в сигнатуре, но вызывают ошибки
                filtered_kwargs = {}
                
                for key, value in kwargs.items():
                    # Не добавляем известные проблемные параметры и неизвестные параметры
                    if key in known_problematic_params:
                        logger.info(f"SafeAnthropicWrapper: Пропускаем проблемный параметр: {key}={value}")
                        continue
                    if key not in valid_params and key != 'self':
                        logger.info(f"SafeAnthropicWrapper: Пропускаем неизвестный параметр: {key}={value}")
                        continue
                    filtered_kwargs[key] = value
                
                logger.info(f"SafeAnthropicWrapper: Вызываем оригинальный __init__ с отфильтрованными параметрами: {filtered_kwargs}")
                
                # Вызываем оригинальный конструктор
                try:
                    super().__init__(*args, **filtered_kwargs)
                    logger.info(f"SafeAnthropicWrapper: Успешная инициализация")
                except TypeError as e:
                    # Если все еще возникают ошибки, логируем и пытаемся решить
                    logger.warning(f"SafeAnthropicWrapper: TypeError: {e}")
                    logger.warning(f"SafeAnthropicWrapper: Аргументы: {args}")
                    logger.warning(f"SafeAnthropicWrapper: Отфильтрованные параметры: {filtered_kwargs}")
                    
                    # Создаем минимальный набор параметров
                    minimal_kwargs = {}
                    if 'api_key' in filtered_kwargs:
                        minimal_kwargs['api_key'] = filtered_kwargs['api_key']
                    
                    logger.info(f"SafeAnthropicWrapper: Пробуем с минимальными параметрами: {minimal_kwargs}")
                    super().__init__(*args, **minimal_kwargs)
                    logger.info(f"SafeAnthropicWrapper: Успешная инициализация с минимальными параметрами")
        
        # Экспортируем безопасную версию
        Anthropic = SafeAnthropicWrapper
        
        # Функция для создания клиентов без proxies
        def create_client(api_key=None):
            """
            Создает клиент Anthropic, безопасно удаляя параметр proxies.
            """
            if api_key is None:
                api_key = os.getenv("ANTHROPIC_API_KEY", "")
            
            logger.info(f"Создание клиента через SafeAnthropicWrapper")
            return SafeAnthropicWrapper(api_key=api_key)
        
        # Прямой патч класса Client, если он существует
        if hasattr(original_anthropic, 'Client'):
            original_client_init = original_anthropic.Client.__init__
            
            def patched_client_init(self, *args, **kwargs):
                if 'proxies' in kwargs:
                    logger.info(f"Удаляем proxies из инициализации Client: {kwargs['proxies']}")
                    kwargs.pop('proxies')
                return original_client_init(self, *args, **kwargs)
            
            original_anthropic.Client.__init__ = patched_client_init
            Client = original_anthropic.Client
            logger.info("Патчим original_anthropic.Client.__init__ для удаления параметра proxies")
        
        # Экспортируем другие компоненты оригинального модуля
        for name in dir(original_anthropic):
            if not name.startswith('_') and name != 'Anthropic' and name != 'Client':
                globals()[name] = getattr(original_anthropic, name)
        
        # Экспортируем версию библиотеки
        try:
            __version__ = original_anthropic.__version__
        except AttributeError:
            try:
                import pkg_resources
                __version__ = pkg_resources.get_distribution("anthropic").version
            except Exception:
                __version__ = "unknown"
        
except Exception as e:
    logger.error(f"Ошибка при инициализации anthropic_wrapper: {e}")
    # Пытаемся использовать оригинальный модуль как запасной вариант
    try:
        import anthropic
        logger.warning("Используем оригинальный модуль anthropic без патчей")
        Anthropic = anthropic.Anthropic
        Client = anthropic.Client if hasattr(anthropic, 'Client') else None
        
        # Функция для безопасного создания клиента
        def create_client(api_key=None):
            if not api_key:
                api_key = os.getenv("ANTHROPIC_API_KEY", "")
            
            logger.info("Создание клиента Anthropic через базовую библиотеку")
            return Anthropic(api_key=api_key)
        
    except ImportError:
        logger.error("Не удалось импортировать ни safe_anthropic, ни оригинальный модуль anthropic")
        raise

# Версия библиотеки
try:
    import pkg_resources
    anthropic_version = pkg_resources.get_distribution("anthropic").version
    logger.info(f"Версия библиотеки anthropic: {anthropic_version}")
except Exception as e:
    logger.warning(f"Не удалось определить версию библиотеки anthropic: {e}")
    anthropic_version = "unknown"

# Проверяем, загружен ли модуль успешно
if Anthropic:
    logger.info(f"Антропик обертка успешно инициализирована (класс: {Anthropic.__name__})")
    print("[ANTHROPIC WRAPPER] Безопасная обертка для библиотеки Anthropic успешно инициализирована!")
else:
    logger.error("Не удалось инициализировать антропик обертку")
    print("[ANTHROPIC WRAPPER ERROR] Не удалось создать безопасную обертку для Anthropic!") 