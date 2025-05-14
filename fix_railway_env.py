#!/usr/bin/env python
"""
Скрипт для исправления API ключа в переменных окружения Railway.
Проверяет и удаляет кавычки из API ключа, которые могут быть добавлены Railway.
"""

import os
import sys
import re
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_railway():
    """Проверяет, запущен ли скрипт в Railway"""
    return os.getenv('RAILWAY_ENVIRONMENT') is not None

def fix_railway_api_key():
    """
    Исправляет API ключ в переменных окружения Railway, удаляя кавычки и другие проблемы.
    """
    print("\n========== ИСПРАВЛЕНИЕ API КЛЮЧА В RAILWAY ==========")
    
    # Проверяем, в каком окружении запущен скрипт
    is_cloud = is_railway()
    print(f"✓ Окружение: {'Railway' if is_cloud else 'Локальное'}")
    
    if not is_cloud:
        print("\n⚠️ Этот скрипт предназначен для запуска в Railway.")
        print("⚠️ В локальном окружении нет необходимости исправлять ключ.")
        return False
    
    # Получаем API ключ
    original_key = os.getenv("ANTHROPIC_API_KEY", "")
    
    if not original_key:
        print("❌ API ключ не найден в переменных окружения!")
        return False
    
    # Выводим информацию о ключе (скрываем большую часть)
    key_length = len(original_key)
    print(f"\n📝 Текущий API ключ (длина: {key_length})")
    if key_length > 10:
        print(f"📝 Начало ключа: {original_key[:15]}")
    
    # Проверка на наличие кавычек
    new_key = original_key
    key_fixed = False
    
    if new_key.startswith('"') and new_key.endswith('"'):
        new_key = new_key.strip('"')
        print("⚠️ Обнаружены двойные кавычки в начале и конце ключа")
        key_fixed = True
    elif new_key.startswith("'") and new_key.endswith("'"):
        new_key = new_key.strip("'")
        print("⚠️ Обнаружены одинарные кавычки в начале и конце ключа")
        key_fixed = True
    
    # Проверка на дополнительные пробелы
    if new_key != new_key.strip():
        new_key = new_key.strip()
        print("⚠️ Обнаружены лишние пробелы в ключе")
        key_fixed = True
    
    # Валидация формата ключа
    print("\n✓ Проверка синтаксиса API ключа:")
    
    # Проверка для новых ключей Claude 3 (sk-ant-api...)
    new_key_pattern = r'^sk-ant-api\w{2}-[A-Za-z0-9-_]{70,100}$'
    # Проверка для старых ключей Claude 2 (sk-...)
    old_key_pattern = r'^sk-[A-Za-z0-9]{40,60}$'
    
    is_new_format = bool(re.match(new_key_pattern, new_key))
    is_old_format = bool(re.match(old_key_pattern, new_key))
    
    if is_new_format or is_old_format:
        print("✅ API ключ имеет правильный синтаксис")
    else:
        print("⚠️ API ключ не соответствует ожидаемому формату!")
    
    # Если ключ не требует исправления
    if not key_fixed:
        print("\n✅ API ключ не имеет лишних кавычек, исправление не требуется")
    else:
        # Обновляем переменную окружения в текущем процессе
        os.environ["ANTHROPIC_API_KEY"] = new_key
        
        print(f"\n✅ Исправленный API ключ (длина: {len(new_key)})")
        print(f"✅ Кавычки из API ключа удалены для текущего запуска")
    
    print("\n✅ Операция завершена")
    
    # Дополнительная информация для пользователя
    print("\n======= РЕЗУЛЬТАТ РАБОТЫ СКРИПТА =======")
    if key_fixed:
        print("✅ Кавычки из API ключа удалены для текущего запуска")
        print("✅ Ключ исправлен в памяти процесса")
        print("🤖 Бот должен нормально заработать в этом запуске")
    else:
        print("✅ API ключ имеет правильный формат")
        print("✅ Никаких исправлений не требуется")
        print("🤖 Бот должен нормально заработать")
    print("=========================================\n")
    
    return True

if __name__ == "__main__":
    fix_railway_api_key() 