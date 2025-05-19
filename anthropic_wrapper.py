#!/usr/bin/env python
"""
Обертка для Anthropic API, которая гарантирует, что параметр 'proxies' не будет передан.
Этот скрипт нужно импортировать и использовать вместо прямого импорта библиотеки anthropic.
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
                if 'proxies' in kwargs:
                    logger.info(f"SafeAnthropicWrapper: Удаляем параметр proxies: {kwargs['proxies']}")
                    kwargs.pop('proxies')
                
                # Вызываем оригинальный конструктор
                try:
                    super().__init__(*args, **kwargs)
                    logger.info(f"SafeAnthropicWrapper: Успешная инициализация")
                except TypeError as e:
                    if "unexpected keyword argument" in str(e):
                        # Если есть еще неизвестные аргументы, логируем их
                        logger.warning(f"SafeAnthropicWrapper: TypeError: {e}")
                        logger.warning(f"SafeAnthropicWrapper: Аргументы: {args}")
                        logger.warning(f"SafeAnthropicWrapper: Параметры: {kwargs}")
                        
                        # Пытаемся определить и удалить проблемные аргументы
                        valid_params = inspect.signature(original_anthropic.Anthropic.__init__).parameters
                        valid_param_names = set(valid_params.keys())
                        
                        # Удаляем все параметры, которых нет в сигнатуре
                        unknown_params = set(kwargs.keys()) - valid_param_names
                        for param in unknown_params:
                            logger.info(f"SafeAnthropicWrapper: Удаляем неизвестный параметр: {param}={kwargs[param]}")
                            kwargs.pop(param)
                        
                        # Пробуем снова с очищенными параметрами
                        super().__init__(*args, **kwargs)
                        logger.info(f"SafeAnthropicWrapper: Успешная инициализация после удаления неизвестных параметров")
                    else:
                        # Другие ошибки пробрасываем
                        raise
        
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
        
        # Экспортируем другие компоненты оригинального модуля
        for name in dir(original_anthropic):
            if not name.startswith('_') and name != 'Anthropic':
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