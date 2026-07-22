#!/bin/bash

# Устанавливаем строгий режим для обработки ошибок
set -e  # выход при ошибке
set -u  # выход при неопределённой переменной

# Цветной вывод для лучшей читаемости
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Функция проверки существования файла
check_file() {
    if [ ! -f "$1" ]; then
        echo -e "${RED}❌ Ошибка: Файл $1 не найден!${NC}"
        return 1
    fi
    if [ ! -x "$1" ] && [[ ! "$1" =~ \.py$ ]]; then
        echo -e "${YELLOW}⚠️  Внимание: Файл $1 не имеет прав на выполнение${NC}"
        echo "Попытка запуска через интерпретатор..."
    fi
    return 0
}

# Функция запуска скрипта
run_script() {
    local script="$1"
    local script_name=$(basename "$script")
    
    echo -e "\n${BLUE}════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}▶ Запуск: $script_name${NC}"
    echo -e "${BLUE}Полный путь: $script${NC}"
    log "Начало выполнения"
    
    # Определяем тип файла и запускаем
    if [[ "$script" == *.py ]]; then
        # Python скрипт
        if command -v python3 &> /dev/null; then
            if python3 "$script"; then
                echo -e "${GREEN}✅ Скрипт $script_name успешно завершён${NC}"
                return 0
            else
                echo -e "${RED}❌ Ошибка в скрипте $script_name (код: $?)${NC}"
                return 1
            fi
        else
            echo -e "${RED}❌ Python3 не найден в системе!${NC}"
            return 1
        fi
    else
        # Bash скрипт
        if [ -x "$script" ]; then
            if "$script"; then
                echo -e "${GREEN}✅ Скрипт $script_name успешно завершён${NC}"
                return 0
            else
                echo -e "${RED}❌ Ошибка в скрипте $script_name (код: $?)${NC}"
                return 1
            fi
        else
            # Если нет прав на выполнение, пробуем через bash
            if bash "$script"; then
                echo -e "${GREEN}✅ Скрипт $script_name успешно завершён${NC}"
                return 0
            else
                echo -e "${RED}❌ Ошибка в скрипте $script_name (код: $?)${NC}"
                return 1
            fi
        fi
    fi
}

echo -e "${YELLOW}════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}    ЗАПУСК ПОСЛЕДОВАТЕЛЬНОГО ВЫПОЛНЕНИЯ СКРИПТОВ${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════${NC}"
echo ""

# Список скриптов для выполнения
scripts=(
    "/home/and/pars5/scrab.py"
    "/home/and/pars5/workv2.sh"
    "/home/and/pars5/ex6.sh"
    "/home/and/pars5/tgbot_scrn.sh"
)

# Проверка всех файлов перед запуском
echo -e "${BLUE}Проверка наличия файлов...${NC}"
for script in "${scripts[@]}"; do
    if ! check_file "$script"; then
        echo -e "${RED}Прерывание выполнения из-за отсутствия файла${NC}"
        exit 1
    fi
done

echo -e "${GREEN}Все файлы найдены. Начинаем выполнение...${NC}\n"

# Счётчик для статистики
total=${#scripts[@]}
completed=0
failed=0

# Запускаем скрипты по очереди
for script in "${scripts[@]}"; do
    if run_script "$script"; then
        ((completed++))
    else
        ((failed++))
        echo -e "${RED}❌ Критическая ошибка в скрипте!${NC}"
        echo -e "${YELLOW}Прерывание выполнения...${NC}"
        break
    fi
    
    # Небольшая пауза между скриптами для стабильности
    if [ "$script" != "${scripts[-1]}" ]; then
        echo -e "${YELLOW}⏳ Ожидание 2 секунды перед следующим скриптом...${NC}"
        sleep 2
    fi
done

# Итоговая статистика
echo -e "\n${YELLOW}════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}                  РЕЗУЛЬТАТЫ ВЫПОЛНЕНИЯ${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════${NC}"
echo -e "Всего скриптов: ${BLUE}$total${NC}"
echo -e "Выполнено успешно: ${GREEN}$completed${NC}"
echo -e "С ошибками: ${RED}$failed${NC}"
echo -e "Время завершения: $(date '+%Y-%m-%d %H:%M:%S')"

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}✅ ВСЕ СКРИПТЫ УСПЕШНО ВЫПОЛНЕНЫ!${NC}"
else
    echo -e "${RED}❌ ВЫПОЛНЕНИЕ ЗАВЕРШЕНО С ОШИБКАМИ${NC}"
    exit 1
fi

echo -e "${YELLOW}════════════════════════════════════════════════════════${NC}"