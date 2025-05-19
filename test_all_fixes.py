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

# Вспомогательная функция для очистки модулей перед тестами
def clean_modules():
    """Удаляет импортированные модули для чистого старта каждого теста"""
    for module in ["anthropic", "safe_anthropic", "anthropic_wrapper", "direct_fix"]:
        if module in sys.modules:
            del sys.modules[module]
    
    return True

# Функция для тестирования каждого метода отдельно
def test_method(name, test_func):
    """Выполняет тест метода с логированием результатов"""
    logger.info(f"==== Тестирование метода {name} ====")
    
    # Очищаем модули перед каждым тестом
    clean_modules()
    
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
        # Запускаем скрипт напрямую для применения патча
        import direct_fix
        
        # Тестируем, создавая клиент с proxies параметром
        from anthropic import Anthropic
        client = Anthropic(
            api_key=API_KEY or "dummy_api_key_for_testing",
            proxies={"http": "http://dummy-proxy.com", "https": None}
        )
        
        # Если дошли до этой точки без ошибок, тест прошел успешно
        logger.info(f"Клиент успешно создан через direct_fix: {type(client).__name__}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при тестировании direct_fix: {e}")
        return False

# 2. Тест безопасной обертки safe_anthropic
def test_safe_anthropic():
    try:
        # Импортируем безопасную обертку
        import safe_anthropic
        
        # Пробуем создать клиент с proxies
        client = safe_anthropic.Anthropic(
            api_key=API_KEY or "dummy_api_key_for_testing",
            proxies={"http": "http://dummy-proxy.com", "https": None}
        )
        
        # Если дошли до этой точки без ошибок, тест прошел успешно
        logger.info(f"Клиент успешно создан через safe_anthropic: {type(client).__name__}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при тестировании safe_anthropic: {e}")
        return False

# 3. Тест комплексной обертки anthropic_wrapper
def test_anthropic_wrapper():
    try:
        # Импортируем обертку
        import anthropic_wrapper
        
        # Создаем клиент с proxies параметром
        client = anthropic_wrapper.Anthropic(
            api_key=API_KEY or "dummy_api_key_for_testing",
            proxies={"http": "http://dummy-proxy.com", "https": None}
        )
        
        # Если дошли до этой точки без ошибок, тест прошел успешно
        logger.info(f"Клиент успешно создан через anthropic_wrapper: {type(client).__name__}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при тестировании anthropic_wrapper непосредственно: {e}")
        
        # Попробуем через функцию-хелпер
        try:
            client = anthropic_wrapper.create_client(api_key=API_KEY or "dummy_api_key_for_testing")
            logger.info(f"Клиент успешно создан через anthropic_wrapper.create_client: {type(client).__name__}")
            return True
        except Exception as helper_error:
            logger.error(f"Ошибка при тестировании anthropic_wrapper.create_client: {helper_error}")
            return False

# 4. Тест комбинированного подхода
def test_combined_approach():
    try:
        # Сначала применяем прямой патч
        import direct_fix
        
        # Затем используем обертку
        import anthropic_wrapper
        
        # Создаем клиент с proxies параметром
        client = anthropic_wrapper.Anthropic(
            api_key=API_KEY or "dummy_api_key_for_testing",
            proxies={"http": "http://dummy-proxy.com", "https": None}
        )
        
        # Если дошли до этой точки без ошибок, тест прошел успешно
        logger.info(f"Клиент успешно создан через комбинированный подход: {type(client).__name__}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при тестировании комбинированного подхода непосредственно: {e}")
        
        # Попробуем через функцию-хелпер
        try:
            client = anthropic_wrapper.create_client(api_key=API_KEY or "dummy_api_key_for_testing")
            logger.info(f"Клиент успешно создан через комбинированный подход с create_client: {type(client).__name__}")
            return True
        except Exception as helper_error:
            logger.error(f"Ошибка при тестировании комбинированного подхода с create_client: {helper_error}")
            return False

# 5. Тест с базовой библиотекой Anthropic (для контроля)
def test_basic_anthropic():
    try:
        # Удаляем все возможные патчи
        clean_modules()
        
        # Импортируем базовую библиотеку
        import anthropic
        
        # Пробуем создать клиент с proxies
        client = anthropic.Anthropic(
            api_key=API_KEY or "dummy_api_key_for_testing",
            proxies={"http": "http://dummy-proxy.com", "https": None}
        )
        
        # Если дошли до этой точки без ошибок - базовая библиотека уже поддерживает proxies
        logger.info(f"ВНИМАНИЕ: Базовая библиотека anthropic работает с параметром proxies: {type(client).__name__}")
        logger.info(f"Версия библиотеки anthropic: {anthropic.__version__ if hasattr(anthropic, '__version__') else 'неизвестно'}")
        return True
    except Exception as e:
        # Это ожидаемое поведение - базовая библиотека не должна работать с proxies
        logger.info(f"Ожидаемая ошибка в базовой библиотеке anthropic: {e}")
        return False

if __name__ == "__main__":
    print("НАЧАЛО ТЕСТИРОВАНИЯ ИСПРАВЛЕНИЙ ДЛЯ ANTHROPIC API")
    print("==================================================")
    
    # Проверяем наличие API ключа
    if not API_KEY:
        logger.warning("⚠️ API ключ не найден в переменных окружения. Тестирование будет использовать фиктивный ключ.")
    
    # Запускаем контрольный тест для проверки базовой библиотеки
    baseline_result = test_method("basic_anthropic", test_basic_anthropic)
    
    # Запускаем все тесты фиксов
    results = {}
    results["direct_fix"] = test_method("direct_fix", test_direct_fix)
    results["safe_anthropic"] = test_method("safe_anthropic", test_safe_anthropic)
    results["anthropic_wrapper"] = test_method("anthropic_wrapper", test_anthropic_wrapper)
    results["combined_approach"] = test_method("combined_approach", test_combined_approach)
    
    # Выводим итоговый результат
    print("\nРЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("=======================")
    
    # Сначала выводим результат базовой библиотеки для контекста
    status = "✅ РАБОТАЕТ С PROXIES" if baseline_result else "❌ НЕ РАБОТАЕТ С PROXIES (ОЖИДАЕМО)"
    print(f"Базовая библиотека: {status}")
    
    # Затем выводим результаты фиксов
    for method, result in results.items():
        status = "✅ УСПЕШНО" if result else "❌ ПРОВАЛ"
        print(f"{method}: {status}")
    
    # Рекомендация на основе результатов тестов
    print("\nРЕКОМЕНДАЦИИ:")
    if baseline_result:
        print("✅ Библиотека anthropic уже поддерживает параметр proxies. Патчи не требуются.")
    elif results["safe_anthropic"]:
        print("✅ РЕКОМЕНДАЦИЯ: Использовать safe_anthropic - самый надежный и простой метод")
        print("   - В скрипте: import safe_anthropic as anthropic")
        print("   - В railway.json: \"startCommand\": \"python safe_anthropic.py && python your_main_script.py\"")
    elif results["direct_fix"]:
        print("✅ РЕКОМЕНДАЦИЯ: Использовать direct_fix - работает на низком уровне")
        print("   - В railway.json: \"startCommand\": \"python direct_fix.py && python your_main_script.py\"")
    elif results["anthropic_wrapper"]:
        print("✅ РЕКОМЕНДАЦИЯ: Использовать anthropic_wrapper")
        print("   - В скрипте: import anthropic_wrapper as anthropic")
        print("   - Создавать клиент через: anthropic.create_client()")
    elif results["combined_approach"]:
        print("✅ РЕКОМЕНДАЦИЯ: Использовать комбинированный подход")
        print("   - В railway.json: \"startCommand\": \"python direct_fix.py && python your_main_script.py\"")
        print("   - В скрипте: import anthropic_wrapper as anthropic")
    else:
        print("❌ ВНИМАНИЕ: Ни один метод не работает корректно. Требуется дополнительная отладка.")
        print("   Рекомендуется обновить библиотеку anthropic или использовать альтернативный API.")
    
    # Определяем успешность тестов
    successful_fixes = sum(1 for result in results.values() if result)
    
    # Выводим итоговый статус
    print("\nСТАТИСТИКА:")
    print(f"- Базовая библиотека поддерживает proxies: {'Да' if baseline_result else 'Нет'}")
    print(f"- Успешных фиксов: {successful_fixes} из {len(results)}")
    
    print("\nТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    
    # Возвращаем успех, если хотя бы один метод работает
    sys.exit(0 if successful_fixes > 0 else 1) 