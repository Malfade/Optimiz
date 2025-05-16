import os
import glob
import re

def fix_proxies_in_files():
    """Ищет и исправляет параметр proxies в вызовах Anthropic API во всех Python файлах"""
    # Ищем все Python файлы в текущей директории и поддиректориях
    python_files = glob.glob("**/*.py", recursive=True)
    
    # Паттерн для поиска создания клиента Anthropic с proxies
    pattern = r'anthropic\.Anthropic\(.*?proxies\s*=\s*[^)]*\)'
    
    fixed_count = 0
    for file_path in python_files:
        try:
            # Пропускаем этот файл
            if file_path == os.path.basename(__file__):
                continue
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Ищем проблемный шаблон
            matches = re.findall(pattern, content, re.DOTALL)
            if matches:
                print(f"Найдено {len(matches)} совпадений в файле {file_path}")
                
                # Заменяем proxies параметр
                for match in matches:
                    fixed = re.sub(r',\s*proxies\s*=\s*[^,)]*', '', match)
                    content = content.replace(match, fixed)
                
                # Записываем исправленное содержимое
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                print(f"✅ Файл {file_path} исправлен")
                fixed_count += 1
        except Exception as e:
            print(f"Ошибка при обработке файла {file_path}: {e}")
    
    return fixed_count

if __name__ == "__main__":
    count = fix_proxies_in_files()
    if count > 0:
        print(f"✅ Всего исправлено файлов: {count}")
    else:
        print("ℹ️ Параметр proxies не найден в файлах проекта")