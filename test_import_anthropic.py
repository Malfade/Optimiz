#!/usr/bin/env python
"""
Тестирует импорт библиотеки anthropic и создание клиента 
с различными стратегиями обхода проблемы proxies.
"""
import os
import sys
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Имитация Railway - только для тестирования
def simulate_railway_env():
    """Имитирует переменные окружения Railway"""
    os.environ['RAILWAY_ENVIRONMENT'] = 'development'
    os.environ['RAILWAY_SERVICE_NAME'] = 'test-service'
    # Для тестирования без реальных прокси установим пустые значения
    os.environ['HTTP_PROXY'] = ''
    os.environ['HTTPS_PROXY'] = ''
    logger.info("Активирована имитация среды Railway")

# Тест 1: С использованием патча fix_railway_anthropic
def test_with_patch():
    """Тестирует использование патча fix_railway_anthropic"""
    logger.info("=== Тест 1: С использованием патча fix_railway_anthropic ===")
    try:
        import fix_railway_anthropic
        logger.info("Патч успешно импортирован")
        
        import anthropic
        logger.info(f"Модуль anthropic успешно импортирован")
        logger.info(f"Содержимое модуля anthropic: {dir(anthropic)}")
        
        # Проверка создания клиента
        try:
            if hasattr(anthropic, 'Anthropic'):
                # Используем правильный формат проксей
                client = anthropic.Anthropic(api_key="test_key", proxies={"http://": None})
                logger.info("✅ Клиент успешно создан через Anthropic")
            elif hasattr(anthropic, 'Client'):
                client = anthropic.Client(api_key="test_key", proxies={"http://": None})
                logger.info("✅ Клиент успешно создан через Client")
            else:
                logger.warning("❌ Не найден класс Anthropic или Client")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при создании клиента: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка при тесте с патчем: {e}")
        return False

# Тест 2: С использованием safe_anthropic
def test_with_safe_anthropic():
    """Тестирует использование safe_anthropic"""
    logger.info("=== Тест 2: С использованием safe_anthropic ===")
    try:
        import safe_anthropic as anthropic
        logger.info("Модуль safe_anthropic успешно импортирован")
        
        # Проверка создания клиента
        try:
            if hasattr(anthropic, 'Anthropic'):
                client = anthropic.Anthropic(api_key="test_key", proxies={"http://": None})
                logger.info("✅ Клиент успешно создан через Anthropic")
            elif hasattr(anthropic, 'Client'):
                client = anthropic.Client(api_key="test_key", proxies={"http://": None})
                logger.info("✅ Клиент успешно создан через Client")
            elif hasattr(anthropic, 'create_client'):
                client = anthropic.create_client(api_key="test_key")
                logger.info("✅ Клиент успешно создан через create_client")
            else:
                logger.warning("❌ Не найден подходящий метод создания клиента")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при создании клиента: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка при тесте с safe_anthropic: {e}")
        return False

# Тест 3: С использованием anthropic_wrapper
def test_with_anthropic_wrapper():
    """Тестирует использование anthropic_wrapper"""
    logger.info("=== Тест 3: С использованием anthropic_wrapper ===")
    try:
        import anthropic_wrapper as anthropic
        logger.info("Модуль anthropic_wrapper успешно импортирован")
        
        # Проверка создания клиента
        try:
            if hasattr(anthropic, 'Anthropic'):
                client = anthropic.Anthropic(api_key="test_key", proxies={"http://": None})
                logger.info("✅ Клиент успешно создан через Anthropic")
            elif hasattr(anthropic, 'create_client'):
                client = anthropic.create_client(api_key="test_key")
                logger.info("✅ Клиент успешно создан через create_client")
            else:
                logger.warning("❌ Не найден подходящий метод создания клиента")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при создании клиента: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка при тесте с anthropic_wrapper: {e}")
        return False

# Тест 4: Комбинированный подход из main.py
def test_main_approach():
    """Тестирует комбинированный подход из main.py"""
    logger.info("=== Тест 4: Комбинированный подход из main.py ===")
    try:
        # Применяем патч для Railway перед импортом anthropic
        import fix_railway_anthropic
        logger.info("Патч для Railway успешно загружен")
        
        # Затем импортируем безопасную версию anthropic
        try:
            # Пробуем использовать безопасную обертку
            import safe_anthropic as anthropic
            logger.info("Импортирована безопасная версия anthropic")
        except ImportError:
            try:
                # Запасной вариант - использовать другую обертку
                import anthropic_wrapper as anthropic
                logger.info("Импортирована обертка anthropic_wrapper")
            except ImportError:
                # Если не удалось, используем оригинальную библиотеку
                logger.warning("Не удалось импортировать безопасные обертки, используем оригинальную библиотеку")
                import anthropic
        
        # Проверка создания клиента
        try:
            if hasattr(anthropic, 'Anthropic'):
                client = anthropic.Anthropic(api_key="test_key", proxies={"http://": None})
                logger.info("✅ Клиент успешно создан через Anthropic")
            elif hasattr(anthropic, 'create_client'):
                client = anthropic.create_client(api_key="test_key")
                logger.info("✅ Клиент успешно создан через create_client")
            else:
                logger.warning("❌ Не найден подходящий метод создания клиента")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при создании клиента: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка при комбинированном подходе: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Тестирование различных стратегий импорта библиотеки anthropic")
    
    # Имитируем среду Railway
    simulate_railway_env()
    
    # Запускаем тесты
    results = {
        "Тест 1 (патч)": test_with_patch(),
        "Тест 2 (safe_anthropic)": test_with_safe_anthropic(),
        "Тест 3 (anthropic_wrapper)": test_with_anthropic_wrapper(),
        "Тест 4 (подход из main.py)": test_main_approach()
    }
    
    # Выводим результаты
    print("\n📊 Результаты тестов:")
    for test_name, result in results.items():
        print(f"{test_name}: {'✅ Успешно' if result else '❌ Ошибка'}")
    
    # Общий результат
    if all(results.values()):
        print("\n🎉 Все тесты пройдены успешно!")
        sys.exit(0)
    else:
        print("\n⚠️ Некоторые тесты не пройдены!")
        sys.exit(1) 