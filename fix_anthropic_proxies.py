import os
   
   # Путь к файлу
file_path = "optimization_bot.py"
   
   # Чтение файла
with open(file_path, "r", encoding="utf-8") as file:
       content = file.read()
   
# Заменяем проблемную часть
if "proxies=proxies" in content:
       content = content.replace("proxies=proxies", "")
   
   # Записываем исправленное содержимое
with open(file_path, "w", encoding="utf-8") as file:
       file.write(content)
   
print("✅ Параметр proxies удален из настроек клиента Anthropic")