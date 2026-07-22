#!/bin/bash

# ============================================
# Парсер информации о местах в поезде (упрощённый)
# ============================================

INPUT_FILE="/home/and/pars5/snapshot/train.html"
OUTPUT_FILE="/home/and/pars5/snapshot/result.txt"

if [[ ! -f "$INPUT_FILE" ]]; then
    echo "Ошибка: Файл '$INPUT_FILE' не найден!"
    exit 1
fi

# Находим все строки с "seats_item"
SEATS_LINES=($(grep -n "seats_item" "$INPUT_FILE" | cut -d: -f1))

# Функция для извлечения данных
extract_data() {
    local line_num="$1"
    local type_name="$2"
    
    local block=$(sed -n "${line_num},$((line_num+15))p" "$INPUT_FILE")
    local seats_line=$(echo "$block" | grep -A 1 "train_seats_count" | tail -1)
    
    local seats=$(echo "$seats_line" | sed 's/&nbsp;/ /g' | grep -o '[0-9]*' | grep -v '^$')
    local seats_array=($seats)
    
    local lower=0
    local upper=0
    
    if [[ ${#seats_array[@]} -ge 2 ]]; then
        lower=${seats_array[0]}
        upper=${seats_array[1]}
    elif [[ ${#seats_array[@]} -eq 1 ]]; then
        lower=${seats_array[0]}
        upper=0
    fi
    
    echo "$type_name: нижних $lower, верхних $upper"
}

# Очищаем выходной файл
> "$OUTPUT_FILE"

# Извлекаем данные
if [[ ${#SEATS_LINES[@]} -ge 3 ]]; then
    echo "Плацкарт: нижних $(extract_data "${SEATS_LINES[0]}" "" | grep -o 'нижних [0-9]*' | grep -o '[0-9]*'), верхних $(extract_data "${SEATS_LINES[0]}" "" | grep -o 'верхних [0-9]*' | grep -o '[0-9]*')" >> "$OUTPUT_FILE"
    echo "Купе: нижних $(extract_data "${SEATS_LINES[1]}" "" | grep -o 'нижних [0-9]*' | grep -o '[0-9]*'), верхних $(extract_data "${SEATS_LINES[1]}" "" | grep -o 'верхних [0-9]*' | grep -o '[0-9]*')" >> "$OUTPUT_FILE"
    echo "СВ: нижних $(extract_data "${SEATS_LINES[2]}" "" | grep -o 'нижних [0-9]*' | grep -o '[0-9]*'), верхних $(extract_data "${SEATS_LINES[2]}" "" | grep -o 'верхних [0-9]*' | grep -o '[0-9]*')" >> "$OUTPUT_FILE"
fi

cat "$OUTPUT_FILE"
