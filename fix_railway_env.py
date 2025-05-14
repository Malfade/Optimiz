#!/usr/bin/env python
"""
Скрипт для исправления API ключа в переменных окружения Railway.
Удаляет лишние кавычки, добавляемые Railway к переменным окружения.
"""

import os
import sys
import re
import logging
from dotenv import load_dotenv, set_key

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger("fix_railway_env")

def is_railway():
    """
    Проверяет, запущен ли скрипт в Railway
    """
    return os.getenv('RAILWAY_ENVIRONMENT') is not None

def fix_api_key_quotes():
    """
    Проверяет и исправляет API ключ Anthropic, удаляя лишние кавычки
    """
    print("\n========== ИСПРАВЛЕНИЕ API КЛЮЧА В RAILWAY ==========")
    
    # Загружаем переменные окружения
    load_dotenv()
    
    is_in_railway = is_railway()
    print(f"✓ Окружение: {'Railway' if is_in_railway else 'Локальное'}")
    
    # Получаем оригинальный ключ
    original_key = os.getenv("ANTHROPIC_API_KEY", "")
    
    if not original_key:
        print("❌ API ключ не найден в переменных окружения!")
        return False
    
    print(f"📝 Текущий API ключ (длина: {len(original_key)})")
    print(f"📝 Начало ключа: {original_key[:15]}")
    
    # Проверяем наличие кавычек
    has_quotes = False
    new_key = original_key
    
    if original_key.startswith('"') and original_key.endswith('"'):
        print("⚠️ Обнаружены двойные кавычки в начале и конце ключа")
        new_key = original_key.strip('"')
        has_quotes = True
    elif original_key.startswith("'") and original_key.endswith("'"):
        print("⚠️ Обнаружены одинарные кавычки в начале и конце ключа")
        new_key = original_key.strip("'")
        has_quotes = True
    
    # Если кавычек нет
    if not has_quotes:
        print("✅ API ключ не имеет лишних кавычек, исправление не требуется")
        return True
    
    # Проверяем новый ключ
    print(f"📝 Исправленный API ключ (длина: {len(new_key)})")
    print(f"📝 Начало ключа: {new_key[:15]}")
    
    # Исправляем переменную окружения в текущем процессе
    os.environ["ANTHROPIC_API_KEY"] = new_key
    
    # Если мы в Railway, сообщаем о процессе исправления
    if is_in_railway:
        print("\n🔧 ИСПРАВЛЕНИЕ В RAILWAY:")
        print("✅ API ключ ИСПРАВЛЕН для текущего запуска")
        print("✅ Бот должен заработать в этом запуске")
        print("⚠️ Для постоянного решения исправьте ключ в панели управления Railway:")
        print("1. Зайдите в Variables на сайте Railway")
        print("2. Удалите кавычки из ANTHROPIC_API_KEY")
    else:
        # В локальном окружении можно обновить .env файл
        try:
            env_path = ".env"
            if not os.path.exists(env_path):
                print(f"❌ Файл {env_path} не найден")
                return True  # Все равно возвращаем True, так как в текущем процессе ключ исправлен
            
            set_key(env_path, "ANTHROPIC_API_KEY", new_key)
            print(f"✅ API ключ успешно обновлен в файле {env_path}")
        except Exception as e:
            print(f"❌ Ошибка при обновлении API ключа в файле: {e}")
    
    return True

def check_api_syntax():
    """
    Проверяет синтаксически корректен ли API ключ
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    
    if not api_key:
        print("❌ API ключ не найден")
        return False
    
    # Проверка на наличие спецсимволов, которые могут быть добавлены Railway
    special_chars = ['"', "'", "\\", "\n", "\r", "\t"]
    found_chars = []
    
    for char in special_chars:
        if char in api_key:
            found_chars.append(char)
    
    if found_chars:
        print(f"⚠️ Обнаружены специальные символы в API ключе: {', '.join(repr(c) for c in found_chars)}")
        return False
    
    # Проверяем начало ключа
    if not (api_key.startswith("sk-") or api_key.startswith("sk-ant-api")):
        print(f"⚠️ API ключ имеет неправильный префикс: {api_key[:10]}")
        return False
    
    print("✅ API ключ имеет правильный синтаксис")
    return True

if __name__ == "__main__":
    if fix_api_key_quotes():
        print("\n✓ Проверка синтаксиса API ключа:")
        check_api_syntax()
        print("\n✅ Операция завершена")
        
        # Добавляем явное сообщение для Railway
        if is_railway():
            print("\n======= РЕЗУЛЬТАТ РАБОТЫ СКРИПТА =======")
            print("✅ Кавычки из API ключа удалены для текущего запуска")
            print("✅ Ключ исправлен в памяти процесса")
            print("🤖 Бот должен нормально заработать в этом запуске")
            print("=========================================")
    else:
        print("\n❌ Операция завершена с ошибками") 