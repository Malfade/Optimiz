#!/usr/bin/env python
"""
Скрипт для проверки API ключа Anthropic.
Проверяет валидность API ключа и возможность подключения к API.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv
import pkg_resources

# Импортируем вспомогательные функции из нашего модуля
from anthropic_helper import get_api_key_with_prefix, is_valid_anthropic_key, create_anthropic_client

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger("test_api_key")

async def test_api_key():
    """
    Проверяет API ключ Anthropic, его формат и возможность подключения к API.
    """
    print("\n========== ТЕСТ API КЛЮЧА ANTHROPIC ==========")
    
    # Загружаем переменные окружения
    load_dotenv()
    
    try:
        print("✅ Модуль anthropic_helper успешно импортирован")
        
        # Импортируем anthropic для проверки версии
        import anthropic
        print(f"📝 Установлена библиотека anthropic версии {anthropic.__version__}")
        if int(anthropic.__version__.split('.')[0]) >= 1 or int(anthropic.__version__.split('.')[1]) >= 5:
            print(f"🔵 Используется новая версия API ({anthropic.__version__}+)")
        else:
            print(f"🟠 Используется старая версия API ({anthropic.__version__})")
        
        # Получаем API ключ
        api_key = get_api_key_with_prefix()
        
        if not api_key:
            print("❌ API ключ не найден в переменных окружения!")
            print("🔧 Добавьте ANTHROPIC_API_KEY в .env файл или переменные окружения")
            return False
        
        # Выводим информацию о ключе (частично скрытую)
        hidden_key = f"{api_key[:10]}..."
        print(f"📝 API ключ успешно получен (длина: {len(api_key)})")
        print(f"📝 Начало ключа: {hidden_key}")
        
        # Проверяем формат ключа
        is_valid = is_valid_anthropic_key(api_key)
        print(f"🔍 Проверка формата ключа: {'✅ Валидный' if is_valid else '❌ Невалидный'}")
        
        if not is_valid:
            print("\n⚠️ API ключ не соответствует ожидаемому формату!")
            print("🔎 Формат нового ключа: 'sk-ant-api03-...'")
            print("🔎 Формат старого ключа: 'sk-...'")
            print("⚠️ Возможно, API ключ содержит лишние символы или неправильно скопирован")
            print("🔧 Рекомендуется создать новый ключ на сайте Anthropic и обновить его")
        
        print("\n📡 Создание клиента Anthropic...")
        # Создаем клиент API
        client, method_name, error_message = await create_anthropic_client()
        
        if error_message:
            print(f"❌ Ошибка при создании клиента: {error_message}")
            return False
        
        print(f"✅ Клиент успешно создан, используется метод: {method_name}")
        
        # Проводим тестовый запрос
        print("\n📡 Тестирование API-соединения...")
        
        try:
            if method_name == "completion":
                # Старый метод API
                response = client.completion(
                    prompt="\n\nHuman: Привет, это тестовый запрос!\n\nAssistant:",
                    model="claude-1",
                    max_tokens_to_sample=10,
                    temperature=0
                )
                response_text = response.completion
            else:
                # Новый метод API (messages)
                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=10,
                    messages=[
                        {"role": "user", "content": "Привет, это тестовый запрос!"}
                    ]
                )
                response_text = response.content[0].text
            
            print(f"✅ Успешное соединение с API! Ответ: {response_text}")
            print("\n🎉 API ключ работает корректно! Все тесты пройдены успешно.")
            return True
        except Exception as e:
            print(f"❌ Ошибка при выполнении тестового запроса: {e}")
            
            # Анализируем ошибку для более подробного вывода
            error_str = str(e)
            if "401" in error_str:
                print("\n⚠️ Ошибка 401 - Неверный ключ API (Authentication Error)")
                print("🔍 Причины ошибки могут быть следующими:")
                print("1. Ключ API неверный или устарел")
                print("2. Ключ скопирован с ошибками (лишние пробелы, символы)")
                print("3. Ключ от другого сервиса (не от Anthropic)")
                print("\n🔧 Рекомендации:")
                print("- Создайте новый ключ API на сайте https://console.anthropic.com/")
                print("- Убедитесь, что правильно копируете ключ без лишних символов")
                print("- Обновите переменную ANTHROPIC_API_KEY в Railway")
            elif "403" in error_str:
                print("\n⚠️ Ошибка 403 - Отказ в доступе (Forbidden)")
                print("🔍 Возможно у вашего аккаунта закончился кредит или доступ ограничен")
            elif "429" in error_str:
                print("\n⚠️ Ошибка 429 - Слишком много запросов (Rate Limit)")
                print("🔍 Превышен лимит запросов, попробуйте позже")
            elif "timeout" in error_str.lower():
                print("\n⚠️ Ошибка тайм-аута - Сервер не отвечает")
                print("🔍 Проверьте подключение к интернету или попробуйте позже")
            
            return False
    except Exception as e:
        print(f"❌ Общая ошибка при тестировании API ключа: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_api_key())
    if not result:
        print("\n❌ Тест API ключа завершен с ошибками!")
        print("🔧 Рекомендуется запустить update_api_key.py для обновления ключа.")
    sys.exit(0 if result else 1) 