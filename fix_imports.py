#!/usr/bin/env python
"""
Скрипт для исправления импортов и обеспечения работы anthropic без ошибок
Этот файл должен быть импортирован ПЕРЕД любыми импортами anthropic
"""
import os
import sys
import logging
import importlib

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fix_imports")

# Глобальная переменная для отслеживания состояния исправления
patched = False

def patch_anthropic_imports():
    """
    Патчит импорты anthropic, гарантируя, что они всегда работают с fallback_anthropic
    Заменяет sys.modules['anthropic'] на fallback_anthropic, если он не существует
    """
    global patched
    
    if patched:
        logger.info("Импорты anthropic уже исправлены")
        return True
    
    logger.info("Запуск исправления импортов anthropic...")
    
    # Очищаем переменные окружения прокси
    proxy_env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
    saved_proxies = {}
    
    for env_var in proxy_env_vars:
        if env_var in os.environ:
            saved_proxies[env_var] = os.environ[env_var]
            logger.info(f"Удаляем переменную окружения {env_var}: {os.environ[env_var]}")
            del os.environ[env_var]
    
    # Проверяем, доступен ли fallback_anthropic
    try:
        import fallback_anthropic
        logger.info("✅ fallback_anthropic успешно импортирован")
        
        # Заменяем anthropic в sys.modules
        if 'anthropic' in sys.modules:
            logger.info("Заменяем существующий модуль anthropic")
            # Сохраняем оригинальный модуль, если он уже был загружен
            orig_anthropic = sys.modules['anthropic']
            
        # Устанавливаем fallback_anthropic как модуль anthropic
        sys.modules['anthropic'] = fallback_anthropic
        logger.info("✅ fallback_anthropic успешно установлен как модуль anthropic")
        
        patched = True
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при исправлении импортов: {e}")
        return False

# Автоматически исправляем импорты при загрузке модуля
success = patch_anthropic_imports()
if success:
    logger.info("🚀 Исправление импортов anthropic выполнено успешно!")
else:
    logger.error("❌ Не удалось исправить импорты anthropic")

# Экспортируем важные константы для прямого использования
HUMAN_PROMPT = "\n\nHuman: "
AI_PROMPT = "\n\nAssistant: "

if __name__ == "__main__":
    print("Запуск тестов для проверки исправления импортов...")
    
    try:
        import anthropic
        print(f"✅ Модуль anthropic успешно импортирован: {anthropic.__name__}")
        print(f"✅ Версия модуля: {getattr(anthropic, '__version__', 'unknown')}")
        
        # Тестируем создание клиента
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            client = anthropic.Anthropic(api_key=api_key)
            print(f"✅ Клиент anthropic успешно создан: {client.__class__.__name__}")
        else:
            print("⚠️ Нет API ключа для тестирования создания клиента")
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")