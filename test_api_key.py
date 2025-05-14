#!/usr/bin/env python
import anthropic

# Функция для тестирования различных форматов ключей
def test_key_format(raw_key, client_type="Client"):
    """
    Тестирует разные форматы ключей с разными версиями API клиента
    
    Args:
        raw_key: Исходный ключ без префикса
        client_type: Тип клиента ("Client" или "Anthropic")
    """
    formats = [
        ("без префикса", raw_key),
        ("с префиксом sk-", f"sk-{raw_key}"),
        ("с префиксом sk-ant-api03-", f"sk-ant-api03-{raw_key}")
    ]
    
    for desc, key in formats:
        try:
            print(f"\nПробуем ключ {desc}...")
            if client_type == "Client":
                # Для старой версии API (0.3.x-0.5.x)
                client = anthropic.Client(api_key=key)
                print(f"✅ Успешно создан клиент anthropic.Client с ключом {desc}")
            else:
                # Для новой версии API (0.6.x+)
                client = anthropic.Anthropic(api_key=key)
                print(f"✅ Успешно создан клиент anthropic.Anthropic с ключом {desc}")
        except Exception as e:
            print(f"❌ Ошибка с ключом {desc}: {e}")

# Получаем ключ для тестирования
test_key = input("Введите ключ API без префикса: ")

print("\n=== Тестирование с anthropic.Client (версии 0.3.x-0.5.x) ===")
test_key_format(test_key, "Client")

print("\n=== Тестирование с anthropic.Anthropic (версии 0.6.x+) ===")
test_key_format(test_key, "Anthropic") 