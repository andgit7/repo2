#!/bin/bash

# Запуск Python скрипта
echo "Запуск Python скрипта..."
python3 /home/and/parser/pr62.py

# Проверка кода завершения Python скрипта
if [ $? -eq 0 ]; then

    
    # Запуск второго bash скрипта
    /home/and/parser/tgbot2.sh
else
    echo "Ошибка при выполнении Python скрипта. Bash скрипт не будет запущен."
    exit 1
fi


