#!/usr/bin/env python
"""
Патч для решения проблемы с proxies параметром в библиотеке anthropic при работе в Railway.

Этот скрипт перехватывает импорт anthropic и патчит его, чтобы игнорировать проблемы с proxies.
Для использования: import fix_railway_anthropic перед импортом anthropic
"""
import os
import sys
import inspect
import logging
import importlib.util
from importlib.machinery import ModuleSpec
from types import ModuleType
import warnings

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fix_railway_anthropic")

# Очищаем переменные окружения прокси
# Railway добавляет эти переменные автоматически, но они могут вызывать проблемы
proxy_env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
saved_proxies = {}

for var in proxy_env_vars:
    if var in os.environ:
        saved_proxies[var] = os.environ[var]
        logger.info(f"Сохраняем и удаляем переменную окружения {var}")
        del os.environ[var]

# Определение функции обертки для __init__
def patched_init(original_init):
    """
    Создает патч для метода __init__, который удаляет параметр proxies.
    """
    def wrapper(self, *args, **kwargs):
        if 'proxies' in kwargs:
            logger.info(f"Удаляем параметр proxies: {kwargs['proxies']}")
            del kwargs['proxies']

        # Получаем сигнатуру оригинального метода
        sig = inspect.signature(original_init)
        valid_params = set(sig.parameters.keys())

        # Удаляем параметры, которых нет в сигнатуре
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_params}
        
        # Если в kwargs было что-то удалено, кроме proxies, логируем это
        removed = {k: v for k, v in kwargs.items() if k not in filtered_kwargs and k != 'proxies'}
        if removed:
            logger.info(f"Также удалены неизвестные параметры: {removed}")

        try:
            return original_init(self, *args, **filtered_kwargs)
        except Exception as e:
            logger.error(f"Ошибка при инициализации: {e}")
            
            # Пробуем только с api_key, если все еще есть ошибки
            if 'api_key' in filtered_kwargs:
                minimal_kwargs = {'api_key': filtered_kwargs['api_key']}
                logger.info(f"Пробуем с минимальными параметрами: {minimal_kwargs}")
                return original_init(self, *args, **minimal_kwargs)
            else:
                raise
            
    return wrapper

# Мета-импортер, который патчит модуль anthropic
class AnthropicPatcher:
    def __init__(self):
        self.original_anthropic = None
        self.is_patched = False
    
    def find_and_patch_module(self):
        """
        Находит и патчит модуль anthropic, если он уже импортирован.
        """
        if 'anthropic' in sys.modules and not self.is_patched:
            original_module = sys.modules['anthropic']
            self.original_anthropic = original_module
            self.patch_module(original_module)
            self.is_patched = True
            logger.info(f"Модуль anthropic успешно пропатчен (из sys.modules)")
    
    def patch_module(self, module):
        """
        Применяет патч к модулю anthropic.
        """
        if hasattr(module, 'Anthropic'):
            original_init = module.Anthropic.__init__
            module.Anthropic.__init__ = patched_init(original_init)
            logger.info("Пропатчен класс Anthropic.__init__")
        
        if hasattr(module, 'Client'):
            original_init = module.Client.__init__
            module.Client.__init__ = patched_init(original_init)
            logger.info("Пропатчен класс Client.__init__")
        
        # Делаем правки и для создания клиента, если такая функция есть
        if hasattr(module, 'create_client'):
            original_create_client = module.create_client
            
            def patched_create_client(*args, **kwargs):
                if 'proxies' in kwargs:
                    logger.info(f"Удаляем параметр proxies из create_client: {kwargs['proxies']}")
                    del kwargs['proxies']
                return original_create_client(*args, **kwargs)
            
            module.create_client = patched_create_client
            logger.info("Пропатчена функция create_client")

# Создаем и применяем патчер
patcher = AnthropicPatcher()
patcher.find_and_patch_module()

# Монки-патчим sys.meta_path для перехвата будущих импортов anthropic
original_meta_path = sys.meta_path.copy()

class AnthropicFinder:
    def find_spec(self, fullname, path, target=None):
        if fullname == 'anthropic' and not patcher.is_patched:
            # Найдем оригинальный спецификатор модуля
            for finder in original_meta_path:
                if hasattr(finder, 'find_spec'):
                    spec = finder.find_spec(fullname, path, target)
                    if spec is not None:
                        # Создаем обертку для спецификатора
                        def exec_module(module):
                            # Вызываем оригинальную функцию
                            if spec.loader.exec_module:
                                spec.loader.exec_module(module)
                            
                            # Патчим модуль после загрузки
                            patcher.patch_module(module)
                            patcher.is_patched = True
                            
                        # Заменяем функцию exec_module
                        if hasattr(spec.loader, 'exec_module'):
                            original_exec = spec.loader.exec_module
                            spec.loader.exec_module = exec_module
                        
                        return spec
        return None

# Добавляем наш finder в начало meta_path
sys.meta_path.insert(0, AnthropicFinder())

# Логируем успешную инициализацию
logger.info("Патч для anthropic в Railway успешно инициализирован!")

# Если наш патч вызывается напрямую, выводим сообщение
if __name__ == "__main__":
    print("Патч для anthropic в Railway активирован!")
    print(f"Сохраненные переменные прокси: {saved_proxies}")
    
    # Простой тест
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", "ключ-для-теста"))
        print(f"Тестовое создание клиента anthropic успешно! {client.__class__.__name__}")
    except Exception as e:
        print(f"Ошибка при тестовом создании клиента: {e}")
        
    # Восстанавливаем переменные окружения
    print("Восстанавливаем переменные окружения прокси для тестов:")
    for var, value in saved_proxies.items():
        os.environ[var] = value
        print(f"  {var}={value}") 