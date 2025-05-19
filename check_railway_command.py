#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для проверки переменных окружения в Railway
"""

import os
import sys
import json

def check_railway_env():
    """Проверяет переменные окружения в Railway"""
    
    # Выводим все переменные окружения (маскируя секретные значения)
    env_vars = {}
    secret_prefixes = ['API_KEY', 'TOKEN', 'PASSWORD', 'SECRET']
    
    for key, value in os.environ.items():
        # Маскируем секретные значения
        if any(key.startswith(prefix) or key.endswith(prefix) for prefix in secret_prefixes):
            if value and len(value) > 8:
                masked_value = value[:4] + '*' * (len(value) - 8) + value[-4:]
                env_vars[key] = masked_value
            else:
                env_vars[key] = '***masked***'
        else:
            env_vars[key] = value
    
    # Проверяем наличие переменных, связанных с командой запуска
    command_vars = [var for var in os.environ.keys() if 'COMMAND' in var.upper()]
    start_vars = [var for var in os.environ.keys() if 'START' in var.upper()]
    
    # Выводим результаты
    print("=== RAILWAY ENVIRONMENT CHECK ===")
    print(f"Command-related variables: {command_vars}")
    print(f"Start-related variables: {start_vars}")
    print("\nAll environment variables:")
    print(json.dumps(env_vars, indent=2))
    print("\nRuntime info:")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Directory contents: {os.listdir('.')}")
    
    # Проверяем наличие критичных файлов
    critical_files = ['main.py', 'fix_imports.py', 'fallback_anthropic.py', 'safe_anthropic.py']
    missing_files = [f for f in critical_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"\n⚠️ WARNING: Missing critical files: {missing_files}")
    else:
        print("\n✅ All critical files are present")
    
    # Проверяем содержимое Procfile
    if os.path.exists('Procfile'):
        with open('Procfile', 'r') as f:
            procfile_content = f.read()
        print(f"\nProcfile content:")
        print(procfile_content)
    else:
        print("\n⚠️ WARNING: Procfile not found")

if __name__ == "__main__":
    check_railway_env() 