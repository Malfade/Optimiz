import anthropic
import pkg_resources
import os
import sys

print(f"Python version: {sys.version}")
print(f"Anthropic version: {pkg_resources.get_distribution('anthropic').version}")
print(f"Anthropic module path: {anthropic.__file__}")

# Проверяем сигнатуру метода __init__ класса Anthropic
try:
    import inspect
    sig = inspect.signature(anthropic.Anthropic.__init__)
    print(f"Anthropic.__init__ signature: {sig}")
except Exception as e:
    print(f"Ошибка при получении сигнатуры: {e}")

# Проверяем наличие переменной окружения
print(f"RAILWAY_ENVIRONMENT: {os.getenv('RAILWAY_ENVIRONMENT')}") 