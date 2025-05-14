#!/usr/bin/env python
"""
Скрипт для тестирования API ключа Anthropic
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
import pkg_resources

async def test_api_key():
    """
    Тестирует API ключ Anthropic
    """
    print("\n========== ТЕСТ API КЛЮЧА ANTHROPIC ==========")
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Импортируем вспомогательный модуль
    try:
        from anthropic_helper import get_api_key_with_prefix, create_anthropic_client, is_valid_anthropic_key
        print("✅ Модуль anthropic_helper успешно импортирован")
    except ImportError as e:
        print(f"❌ Ошибка импорта модуля anthropic_helper: {e}")
        sys.exit(1)
    
    # Получаем версию библиотеки anthropic
    try:
        anthropic_version = pkg_resources.get_distribution("anthropic").version
        print(f"📝 Установлена библиотека anthropic версии {anthropic_version}")
        
        if anthropic_version.startswith("0.5") and int(anthropic_version.split(".")[1]) >= 10:
            print("🔵 Используется новая версия API (0.5.10+)")
            api_type = "новый"
        elif anthropic_version.startswith("0.") and int(anthropic_version.split(".")[1]) >= 6:
            print("🔵 Используется новая версия API (0.6+)")
            api_type = "новый"
        else:
            print("🟠 Используется старая версия API (до 0.5.10)")
            api_type = "старый"
    except Exception as e:
        print(f"❌ Ошибка определения версии библиотеки: {e}")
        api_type = "неизвестный"
    
    # Получаем API ключ
    try:
        api_key = get_api_key_with_prefix()
        
        if not api_key:
            print("❌ API ключ не найден в переменных окружения!")
            # Пробуем поискать в переменных окружения
            direct_key = os.getenv("ANTHROPIC_API_KEY")
            if direct_key:
                print(f"📝 Найден исходный ключ в ANTHROPIC_API_KEY (длина: {len(direct_key)})")
                print(f"📝 Начало ключа: {direct_key[:7]}...")
                
                # Проверяем формат ключа напрямую
                is_valid = is_valid_anthropic_key(direct_key)
                print(f"🔍 Прямая проверка формата ключа: {'✅ Валидный' if is_valid else '❌ Невалидный'}")
            else:
                print("❌ Ключ ANTHROPIC_API_KEY не найден в переменных окружения!")
            return False
        
        print(f"📝 API ключ успешно получен (длина: {len(api_key)})")
        print(f"📝 Начало ключа: {api_key[:12]}...")
        print(f"🔍 Проверка формата ключа: {'✅ Валидный' if is_valid_anthropic_key(api_key) else '❌ Невалидный'}")
        
        # Проверяем соответствие типа ключа API версии
        if api_type == "новый" and not api_key.startswith("sk-ant-api"):
            print(f"⚠️ ПРЕДУПРЕЖДЕНИЕ: Для {anthropic_version} должен использоваться ключ формата sk-ant-api03-...")
        elif api_type == "старый" and not api_key.startswith("sk-"):
            print(f"⚠️ ПРЕДУПРЕЖДЕНИЕ: Для {anthropic_version} должен использоваться ключ формата sk-...")
    except Exception as e:
        print(f"❌ Ошибка при получении API ключа: {e}")
        return False
    
    # Создаем клиент
    print("\n📡 Создание клиента Anthropic...")
    try:
        client, method, error = await create_anthropic_client()
        
        if error:
            print(f"❌ Ошибка создания клиента: {error}")
            return False
        else:
            print(f"✅ Клиент успешно создан, используется метод: {method}")
    except Exception as e:
        print(f"❌ Ошибка при создании клиента: {e}")
        return False
    
    # Выполняем тестовый запрос
    print("\n📡 Тестирование API-соединения...")
    try:
        if method == "completion":
            # Старое API
            response = client.completion(
                prompt="\n\nHuman: Привет, это тестовый запрос. Ответь одним словом.\n\nAssistant:",
                model="claude-instant-1.2",
                max_tokens_to_sample=20,
                temperature=0
            )
            result = response.completion
        else:
            # Новое API
            messages = [
                {
                    "role": "user", 
                    "content": "Привет, это тестовый запрос. Ответь одним словом."
                }
            ]
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=20,
                temperature=0,
                messages=messages
            )
            result = response.content[0].text
        
        print(f"✅ Тестовый запрос выполнен успешно! Получен ответ: '{result}'")
        print("✅ API ключ полностью функционален!")
        return True
    except Exception as e:
        error_str = str(e)
        print(f"❌ Ошибка при выполнении тестового запроса: {e}")
        
        if "authentication_error" in error_str or "invalid x-api-key" in error_str:
            print("\n⚠️ Ошибка аутентификации! Проблема с API ключом:")
            print("1. Проверьте, что ключ не просрочен")
            print("2. Убедитесь, что у вас есть доступ к API")
            print("3. Используйте утилиту обновления ключа (update_api_key.py)")
        elif "credit balance is too low" in error_str:
            print("\n⚠️ Недостаточно средств на балансе API!")
        
        return False

if __name__ == "__main__":
    result = asyncio.run(test_api_key())
    print("\n================================================")
    
    if result:
        print("✅ Тест API ключа завершен успешно! Ключ работает корректно.")
        sys.exit(0)
    else:
        print("❌ Тест API ключа завершен с ошибками!")
        print("🔧 Рекомендуется запустить update_api_key.py для обновления ключа.")
        sys.exit(1) 