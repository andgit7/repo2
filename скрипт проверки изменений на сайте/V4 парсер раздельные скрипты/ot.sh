#!/bin/bash

# Цветной вывод
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${YELLOW}=== Запуск трёх скриптов по очереди ===${NC}\n"

# Список скриптов
scripts=(
    "/home/and/pars5/workv2.sh"
    "/home/and/pars5/ex6.sh"
    "/home/and/pars5/tgbot_scrn.sh"
)

for script in "${scripts[@]}"; do
    script_name=$(basename "$script")
    echo -e "${GREEN}▶ Запуск: $script_name${NC}"
    echo "Время: $(date '+%H:%M:%S')"
    
    if bash "$script"; then
        echo -e "${GREEN}✅ $script_name - OK${NC}"
    else
        echo -e "${RED}❌ $script_name - ОШИБКА!${NC}"
        echo "Прерывание..."
        exit 1
    fi
    
    echo "---"
    sleep 1
done

echo -e "${GREEN}✅ Все три скрипта выполнены успешно!${NC}"
