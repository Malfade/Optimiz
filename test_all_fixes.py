#!/usr/bin/env python
"""
Комплексный тест всех методов исправления проблемы с параметром proxies
в Anthropic API клиенте.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_fixes")

# Загружаем переменные окружения
load_dotenv()

# Глобальная переменная для хранения API ключа
API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Функция для тестирования каждого метода отдельно
def test_method(name, test_func):
    """Выполняет тест метода с логированием результатов"""
    logger.info(f"==== Тестирование метода {name} ====")
    try:
        result = test_func()
        if result:
            logger.info(f"✅ Метод {name} успешно прошел тестирование!")
            return True
        else:
            logger.error(f"❌ Метод {name} не прошел тестирование")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании метода {name}: {e}")
        return False

# 1. Тест прямого исправления базового HTTP клиента
def test_direct_fix():
    try:
        # Перезагружаем модуль anthropic, чтобы тест был чистым
        if "anthropic" in sys.modules:
            del sys.modules["anthropic"]
        
        # Запускаем прямой патч
        import direct_fix
        
        # Пробуем создать клиент с proxies параметром
        from anthropic import Anthropic
        client = Anthropic(
            api_key=API_KEY,
            proxies={"http": None, "https": None}
        )
        logger.info(f"Клиент успешно создан: {type(client).__name__}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при тестировании прямого исправления: {e}")
        return False

# 2. Тест безопасной обертки safe_anthropic
def test_safe_anthropic():
    try:
        # Перезагружаем модули
        for module in ["anthropic", "safe_anthropic"]:
            if module in sys.modules:
                del sys.modules[module]
        
        # Импортируем безопасную обертку
        import safe_anthropic
        
        # Пробуем создать клиент с proxies
        client = safe_anthropic.Anthropic(
            api_key=API_KEY,
            proxies={"http": None, "https": None}
        )
        logger.info(f"Клиент успешно создан через safe_anthropic: {type(client).__name__}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при тестировании safe_anthropic: {e}")
        return False

# 3. Тест комплексной обертки anthropic_wrapper
def test_anthropic_wrapper():
    try:
        # Перезагружаем модули
        for module in ["anthropic", "safe_anthropic", "anthropic_wrapper"]:
            if module in sys.modules:
                del sys.modules[module]
        
        # Импортируем обертку
        import anthropic_wrapper
        
        # Создаем клиент через функцию-хелпер
        client = anthropic_wrapper.create_client(api_key=API_KEY)
        logger.info(f"Клиент успешно создан через anthropic_wrapper: {type(client).__name__}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при тестировании anthropic_wrapper: {e}")
        return False

# 4. Тест комбинированного подхода
def test_combined_approach():
    try:
        # Перезагружаем модули
        for module in ["anthropic", "safe_anthropic", "anthropic_wrapper"]:
            if module in sys.modules:
                del sys.modules[module]
        
        # Сначала применяем прямой патч
        import direct_fix
        
        # Затем используем обертку
        import anthropic_wrapper
        
        # Создаем клиент через функцию-хелпер
        client = anthropic_wrapper.create_client(api_key=API_KEY)
        logger.info(f"Клиент успешно создан через комбинированный подход: {type(client).__name__}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при тестировании комбинированного подхода: {e}")
        return False

if __name__ == "__main__":
    print("НАЧАЛО ТЕСТИРОВАНИЯ ИСПРАВЛЕНИЙ ДЛЯ ANTHROPIC API")
    print("==================================================")
    
    # Проверяем наличие API ключа
    if not API_KEY:
        logger.warning("⚠️ API ключ не найден в переменных окружения. Тестирование может быть неполным.")
    
    # Запускаем все тесты
    results = {}
    results["direct_fix"] = test_method("direct_fix", test_direct_fix)
    results["safe_anthropic"] = test_method("safe_anthropic", test_safe_anthropic)
    results["anthropic_wrapper"] = test_method("anthropic_wrapper", test_anthropic_wrapper)
    results["combined_approach"] = test_method("combined_approach", test_combined_approach)
    
    # Выводим итоговый результат
    print("\nРЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("=======================")
    for method, result in results.items():
        status = "✅ УСПЕШНО" if result else "❌ ПРОВАЛ"
        print(f"{method}: {status}")
    
    # Рекомендация на основе результатов
    if results["combined_approach"]:
        print("\n✅ РЕКОМЕНДАЦИЯ: Использовать комбинированный подход - сначала direct_fix, затем anthropic_wrapper")
    elif results["direct_fix"]:
        print("\n✅ РЕКОМЕНДАЦИЯ: Использовать direct_fix - наиболее надежное решение")
    elif results["safe_anthropic"] or results["anthropic_wrapper"]:
        print("\n✅ РЕКОМЕНДАЦИЯ: Использовать safe_anthropic или anthropic_wrapper")
    else:
        print("\n❌ ВНИМАНИЕ: Ни один метод не работает корректно. Требуется дополнительная отладка.")
    
    print("\nТЕСТИРОВАНИЕ ЗАВЕРШЕНО") 