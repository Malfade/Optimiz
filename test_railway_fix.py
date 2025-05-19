#!/usr/bin/env python
"""
Тестовый скрипт для проверки работы патча для Railway
"""
import os
import sys

# Устанавливаем переменную окружения для тестирования
os.environ['RAILWAY_ENVIRONMENT'] = 'test'

# Запускаем патч
print("Применяем патч для Railway...")
import fix_railway_anthropic

# Теперь пробуем импортировать и создать клиент anthropic
print("\nПроверяем, работает ли патч...")
try:
    import anthropic
    
    # Пробуем создать клиент с параметром proxies - используем правильный формат URL
    proxies = {'http://': None, 'https://': None}
    client = anthropic.Anthropic(api_key="test_key", proxies=proxies)
    
    print("\n✅ ТЕСТ ПРОЙДЕН! Патч работает корректно.")
    print("Клиент Anthropic успешно создан с параметром proxies.")
    
except Exception as e:
    print(f"\n❌ ТЕСТ НЕ ПРОЙДЕН! Ошибка: {e}")
    print("Патч не работает. Проверьте логи выше для деталей.")
    
print("\nТест завершен.") 