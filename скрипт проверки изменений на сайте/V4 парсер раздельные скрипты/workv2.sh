#!/bin/bash

# ========================================================
# НАСТРОЙКИ СКРИПТА - ИЗМЕНИТЕ ЗДЕСЬ НОМЕР ПОЕЗДА
# ========================================================
TRAIN_NUMBER="018М"  # <-- Сюда впишите нужный номер поезда (с русской буквой)
# ========================================================

# Если номер передан как аргумент командной строки - используем его
if [ ! -z "$1" ]; then
    TRAIN_NUMBER="$1"
fi

INPUT_FILE="/home/and/pars5/snapshot/parsed_page.html"
OUTPUT_FILE="/home/and/pars5/snapshot/train.html"

# Проверяем входной файл
if [ ! -f "$INPUT_FILE" ]; then
    echo "❌ Ошибка: Файл '$INPUT_FILE' не найден!"
    echo "Использование: $0 [номер_поезда] [входной_файл] [выходной_файл]"
    echo "Пример: $0 018М page.html result.html"
    echo "Текущий номер поезда: $TRAIN_NUMBER"
    exit 1
fi

echo "🔍 Обработка файла: $INPUT_FILE"
echo "🔍 Поиск поезда ${TRAIN_NUMBER}..."

# Экранируем спецсимволы для grep
TRAIN_ESCAPED=$(echo "$TRAIN_NUMBER" | sed 's/\([.*+?^${}()|[\]\\]\)/\\\1/g')

# Находим начало блока поезда
START_LINE=$(grep -n "data-number=\"${TRAIN_ESCAPED}" "$INPUT_FILE" | head -1 | cut -d: -f1)

if [ -z "$START_LINE" ]; then
    echo "❌ Поезд ${TRAIN_NUMBER} не найден в файле!"
    echo ""
    echo "Доступные поезда в файле:"
    grep -o 'data-number="[^"]*"' "$INPUT_FILE" | head -10
    exit 1
fi

echo "✅ Найден поезд ${TRAIN_NUMBER} на строке: $START_LINE"

# Создаем временный файл
TEMP_FILE=$(mktemp)

# Используем awk для точного определения конца блока
awk -v start="$START_LINE" -v train="$TRAIN_NUMBER" '
BEGIN { 
    in_block = 0
    div_count = 0
    found_start = 0
    output_line = 0
}
{
    if (NR >= start) {
        # Находим начало блока - первый div с классом train
        if (!found_start && $0 ~ /<div class="train train_seats/) {
            found_start = 1
            in_block = 1
            div_count = 1
            output_line = 1
            print $0
            next
        }
        
        if (in_block) {
            # Считаем все div теги в строке
            line = $0
            
            # Считаем открывающие теги <div>
            temp = line
            while (match(temp, /<div[^>]*>/)) {
                div_count++
                temp = substr(temp, RSTART + RLENGTH)
            }
            
            # Считаем закрывающие теги </div>
            temp = line
            while (match(temp, /<\/div>/)) {
                div_count--
                temp = substr(temp, RSTART + RLENGTH)
            }
            
            # Проверяем, не начался ли новый поезд внутри блока
            if (output_line > 0 && $0 ~ /<div class="train train_seats/ && $0 !~ "data-number=\"" train) {
                # Это новый поезд - значит предыдущий закончился
                in_block = 0
                exit
            }
            
            # Выводим строку
            print $0
            output_line++
            
            # Если мы закрыли все div"ы, выходим
            if (div_count == 0) {
                in_block = 0
                exit
            }
        }
    }
}' "$INPUT_FILE" > "$TEMP_FILE"

# Проверяем результат
if [ -s "$TEMP_FILE" ]; then
    # Проверяем, не захватили ли лишние поезда
    TRAIN_COUNT=$(grep -c "data-number=" "$TEMP_FILE")
    
    if [ "$TRAIN_COUNT" -gt 1 ]; then
        echo "⚠️  Обнаружено несколько поездов ($TRAIN_COUNT), пробуем уточнить..."
        
        # Удаляем все после первого найденного поезда
        # Ищем второе вхождение data-number=
        SECOND_TRAIN_LINE=$(grep -n "data-number=" "$TEMP_FILE" | tail -1 | cut -d: -f1)
        if [ ! -z "$SECOND_TRAIN_LINE" ] && [ "$SECOND_TRAIN_LINE" -gt 1 ]; then
            # Обрезаем файл до второго поезда
            head -n $((SECOND_TRAIN_LINE - 1)) "$TEMP_FILE" > "${TEMP_FILE}.tmp"
            mv "${TEMP_FILE}.tmp" "$TEMP_FILE"
        fi
    fi
    
    # Добавляем заголовок для наглядности
    {
        echo "<!-- ======================================== -->"
        echo "<!-- ПОЕЗД №${TRAIN_NUMBER}                     -->"
        
        # Извлекаем маршрут
        ROUTE=$(grep -o 'data-number="[^"]*"' "$TEMP_FILE" | head -1 | sed 's/data-number="//;s/"//')
        echo "<!-- ${ROUTE} -->"
        
        # Извлекаем дату
        DATE=$(grep -o 'date[^>]*>[0-9][0-9] [а-я]*, [а-я]*' "$TEMP_FILE" | head -1 | sed 's/.*>//')
        if [ ! -z "$DATE" ]; then
            echo "<!-- ДАТА: ${DATE} -->"
        fi
        
        echo "<!-- ======================================== -->"
        echo ""
        cat "$TEMP_FILE"
    } > "$OUTPUT_FILE"
    
    echo "✅ Информация о поезде ${TRAIN_NUMBER} сохранена!"
    echo "📁 Выходной файл: $OUTPUT_FILE"
    echo "📊 Размер: $(wc -c < "$OUTPUT_FILE") байт"
    echo "📊 Количество строк: $(wc -l < "$OUTPUT_FILE")"
    echo ""
    echo "📋 В вырезанном блоке содержится:"
    
    # Проверяем наличие информации о местах
    if grep -q "train_places" "$OUTPUT_FILE"; then
        echo "   ✅ Информация о типах вагонов"
    fi
    if grep -q "train_seats_count" "$OUTPUT_FILE"; then
        echo "   ✅ Информация о количестве свободных мест"
    fi
    if grep -q "train_cost" "$OUTPUT_FILE"; then
        echo "   ✅ Информация о ценах на билеты"
    fi
    
    # Проверяем, не захватили ли лишние поезда
    TRAIN_COUNT_FINAL=$(grep -c "data-number=" "$OUTPUT_FILE")
    if [ "$TRAIN_COUNT_FINAL" -eq 1 ]; then
        echo "   ✅ Вырезан только один поезд"
    else
        echo "   ⚠️  Внимание: вырезано ${TRAIN_COUNT_FINAL} поездов!"
    fi
    
    echo ""
    echo "📋 ИНФОРМАЦИЯ О СВОБОДНЫХ МЕСТАХ:"
    echo "===================================="
    
    # Извлекаем информацию о каждом классе
    grep -A10 "train_places_name" "$OUTPUT_FILE" | grep -E "(train_places_name|train_seats_count|train_cost)" | while read line; do
        if echo "$line" | grep -q "train_places_name"; then
            CLASS=$(echo "$line" | sed 's/.*>\([^<]*\)<.*/\1/')
            echo "🔹 $CLASS:"
        elif echo "$line" | grep -q "train_seats_count"; then
            SEATS=$(echo "$line" | sed 's/.*>\([^<]*\)<.*/\1/')
            echo "   Места: $SEATS"
        elif echo "$line" | grep -q "train_cost"; then
            PRICE=$(echo "$line" | sed 's/.*>\([^<]*\)<.*/\1/')
            echo "   Цена: от $PRICE"
            echo ""
        fi
    done
    
    echo "===================================="
    echo ""
    echo "💡 Для просмотра используйте: cat $OUTPUT_FILE"
else
    echo "❌ Не удалось извлечь информацию"
    rm -f "$TEMP_FILE"
    exit 1
fi

rm -f "$TEMP_FILE"
