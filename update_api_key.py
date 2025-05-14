#!/usr/bin/env python
"""
Скрипт для обновления API ключа Anthropic.
Позволяет обновить ключ API в .env файле и в переменных окружения.
"""

import os
import sys
import re
import logging
from dotenv import load_dotenv, set_key, find_dotenv

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger("update_api_key")

def is_railway():
    """
    Проверяет, запущен ли скрипт в Railway
    """
    return os.getenv('RAILWAY_ENVIRONMENT') is not None

def is_valid_anthropic_key(api_key):
    """
    Проверяет формат API ключа Anthropic
    
    Допустимые форматы:
    - sk-ant-api03-... (новый формат)
    - sk-... (старый формат)
    """
    # Паттерны для проверки
    new_key_pattern = r'^sk-ant-api\d{2}-[a-zA-Z0-9]{24}\.+[a-zA-Z0-9]{16}$'
    old_key_pattern = r'^sk-[a-zA-Z0-9]{64}$'
    
    return bool(re.match(new_key_pattern, api_key) or re.match(old_key_pattern, api_key))

def show_key_format_instructions():
    """
    Показывает инструкции по получению нового API ключа Anthropic
    """
    print("\n📝 КАК ПОЛУЧИТЬ НОВЫЙ API КЛЮЧ ANTHROPIC:")
    print("1. Перейдите на сайт https://console.anthropic.com/")
    print("2. Войдите в свой аккаунт Anthropic (или создайте новый)")
    print("3. Перейдите в раздел API Keys")
    print("4. Нажмите кнопку 'Create key'")
    print("5. Дайте имя вашему ключу (например, 'OptimizationBot')")
    print("6. Выберите разрешения (permissions) - минимум нужен 'text'")
    print("7. Нажмите кнопку 'Create key'")
    print("8. Скопируйте весь ключ полностью - НЕ МЕНЯЙТЕ ЕГО ФОРМАТ!")
    print("9. Ключ имеет формат: sk-ant-api03-xxxxxxxx.xxxxxxxx (новый)")
    print("   или формат: sk-xxxxxxxxxxxx (старый)")
    print("\n⚠️ ВАЖНО: ключ показывается только ОДИН РАЗ при создании!\n")

def update_api_key():
    """
    Обновляет API ключ Anthropic в .env файле и переменных окружения
    """
    print("\n========== ОБНОВЛЕНИЕ API КЛЮЧА ANTHROPIC ==========")
    
    # Определяем, запущены ли мы в Railway
    is_in_railway = is_railway()
    print(f"✓ Окружение: {'Railway' if is_in_railway else 'Локальное'}")
    
    # Загружаем текущие переменные окружения
    dotenv_file = find_dotenv()
    load_dotenv(dotenv_file)
    
    # Получаем текущий API ключ (если есть)
    current_key = os.getenv("ANTHROPIC_API_KEY", "")
    if current_key:
        masked_key = current_key[:10] + "..." + current_key[-5:] if len(current_key) > 20 else current_key[:5] + "..."
        print(f"📝 Текущий API ключ: {masked_key} (длина: {len(current_key)})")
    else:
        print("📝 Текущий API ключ не найден")
    
    # В Railway работаем в автоматическом режиме
    if is_in_railway:
        print("\n🔧 ЗАПУСК В ОКРУЖЕНИИ RAILWAY (автоматический режим)")
        
        if not current_key:
            print("❌ API ключ не найден в переменных окружения Railway!")
            print("⚠️ Необходимо добавить переменную ANTHROPIC_API_KEY в Railway")
            return False
            
        # Проверяем формат ключа
        is_valid = is_valid_anthropic_key(current_key)
        if not is_valid:
            print("⚠️ Формат API ключа не соответствует ожидаемому!")
            print("⚠️ Проверьте ключ в переменных Railway")
        else:
            print("✅ Формат API ключа корректен")
            
        print("\n⚠️ В Railway автоматическое обновление ключа недоступно")
        print("⚠️ Для обновления API ключа выполните следующие шаги:")
        print("1. Получите новый ключ на сайте https://console.anthropic.com/")
        print("2. Обновите переменную ANTHROPIC_API_KEY в Railway")
        
        # Всегда возвращаем True чтобы продолжить выполнение бота
        return True
    
    # Показываем инструкцию по получению ключа для локального режима
    show_key_format_instructions()
    
    # Запрашиваем новый ключ
    new_key = input("\n📝 Введите новый API ключ Anthropic: ").strip()
    
    if not new_key:
        print("❌ Ключ не может быть пустым! Отмена операции.")
        return False
    
    # Проверяем наличие кавычек
    if new_key.startswith('"') and new_key.endswith('"'):
        new_key = new_key.strip('"')
        print("⚠️ Удалены двойные кавычки из ключа")
    elif new_key.startswith("'") and new_key.endswith("'"):
        new_key = new_key.strip("'")
        print("⚠️ Удалены одинарные кавычки из ключа")
    
    # Проверяем формат ключа
    if not is_valid_anthropic_key(new_key):
        print("⚠️ Предупреждение: формат ключа не соответствует ожидаемому!")
        
        # Проверяем, что ключ начинается с правильного префикса
        if not (new_key.startswith("sk-ant-api") or new_key.startswith("sk-")):
            print("❌ Ключ должен начинаться с 'sk-ant-api' или 'sk-'")
            retry = input("Продолжить несмотря на ошибку формата? (y/n): ").lower()
            if retry != 'y':
                print("❌ Операция отменена пользователем.")
                return False
        else:
            print("⚠️ Ключ имеет правильный префикс, но не соответствует точному формату")
            print("⚠️ Это может быть нормально, если Anthropic обновил формат ключей")
    else:
        print("✅ Формат ключа API корректен")
    
    # Обновляем ключ в переменных окружения текущего процесса
    os.environ["ANTHROPIC_API_KEY"] = new_key
    print("✅ API ключ обновлен в текущем процессе")
    
    # Обновляем ключ в .env файле
    try:
        if not dotenv_file:
            # Если .env файл не найден, создаем его
            with open(".env", "w") as f:
                f.write(f"ANTHROPIC_API_KEY={new_key}\n")
            print("✅ Создан новый .env файл с API ключом")
        else:
            # Обновляем существующий .env файл
            set_key(dotenv_file, "ANTHROPIC_API_KEY", new_key)
            print(f"✅ API ключ обновлен в файле {dotenv_file}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при обновлении .env файла: {e}")
        print("⚠️ API ключ обновлен только для текущего процесса")
        return False

if __name__ == "__main__":
    if update_api_key():
        print("\n✅ API ключ успешно обновлен!")
        
        # Проверка нового ключа
        if not is_railway():
            check_key = input("\nПроверить новый ключ с API Anthropic? (y/n): ").lower()
            if check_key == 'y':
                try:
                    import test_api_key
                    import asyncio
                    asyncio.run(test_api_key.test_api_key())
                except ImportError:
                    print("❌ Модуль test_api_key.py не найден!")
                    print("📝 Запустите тест отдельно командой: python test_api_key.py")
    else:
        print("\n❌ Операция завершена с ошибками!") 