#!/usr/bin/env python
"""
Обновление API ключа Anthropic в файле .env
"""

import os
import sys
import re
from dotenv import load_dotenv, set_key

def update_api_key():
    """
    Обновляет API ключ в файле .env, обеспечивая совместимость с версией библиотеки
    """
    print("======== Утилита обновления API ключа ========")
    
    # Загружаем текущие переменные окружения
    load_dotenv()
    
    # Проверяем текущий ключ
    current_key = os.getenv("ANTHROPIC_API_KEY", "")
    if current_key:
        print(f"Текущий ключ найден (длина: {len(current_key)})")
        if not current_key.startswith("sk-ant-api") and not current_key.startswith("sk-"):
            print("⚠️ Текущий ключ не соответствует стандартному формату")
    else:
        print("Текущий ключ не найден")
    
    # Запрашиваем новый ключ
    print("\nВведите новый API ключ Anthropic (оставьте пустым, чтобы отменить):")
    new_key = input("> ").strip()
    
    if not new_key:
        print("Операция отменена пользователем.")
        return False
    
    # Форматируем ключ
    if not new_key.startswith("sk-ant-api"):
        if new_key.startswith("sk-"):
            print("Преобразование ключа из старого формата в новый...")
            new_key = new_key.replace("sk-", "sk-ant-api03-")
        else:
            print("Добавление префикса к ключу...")
            new_key = f"sk-ant-api03-{new_key}"
    
    # Проверяем формат ключа
    print(f"Проверка формата ключа (длина: {len(new_key)})...")
    if not re.match(r'^sk-ant-api03-[A-Za-z0-9]{24,}$', new_key):
        print("⚠️ Предупреждение: формат ключа может быть неправильным")
        print("Ключ должен иметь формат: sk-ant-api03-XXXXXXXXXXXXXXXXXXXX")
        retry = input("Продолжить обновление? (y/n): ").lower()
        if retry != 'y':
            print("Операция отменена пользователем.")
            return False
    
    # Обновляем ключ в .env файле
    try:
        env_path = ".env"
        if not os.path.exists(env_path):
            # Создаем .env файл, если он не существует
            with open(env_path, "w") as f:
                f.write("# Переменные окружения\n")
        
        set_key(env_path, "ANTHROPIC_API_KEY", new_key)
        print(f"✅ API ключ успешно обновлен в файле {env_path}")
        return True
    except Exception as e:
        print(f"❌ Ошибка при обновлении API ключа: {e}")
        return False

if __name__ == "__main__":
    if update_api_key():
        print("✅ Операция завершена успешно")
    else:
        print("❌ Операция завершена с ошибками")
        sys.exit(1)
    
    # Предлагаем проверить ключ
    test_key = input("\nХотите проверить обновленный ключ? (y/n): ").lower()
    if test_key == 'y':
        try:
            os.system("python test_api_key.py")
        except Exception as e:
            print(f"❌ Ошибка при запуске теста: {e}") 