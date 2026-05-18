#!/bin/bash

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Переменные
chatid=376050665
path=/home/and/parser/parsed_grandtrain_ru/index.html
token=7840513805:AAESfH3LIHUn_50fC5NxclX2d9mvoYJxgpw
diff_file=/home/and/parser/zdarova-zaebal.txt
snapshot=/home/and/parser/grand_snapshot.txt
out=/home/and/parser/parsed_grandtrain_ru/out.html
screenshot=/home/and/parser/parsed_grandtrain_ru/index_fullpage.png
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Извлечение нужных строк из index.html
sed -rn 's/.*span>([^<]*(нижних|нижнее)[^<]*).*/\1/p' "$path" > "$out"

# Сравнение с предыдущим снимком, запись отличий в diff_file
diff --changed-group-format='%>' --unchanged-group-format='' "$snapshot" "$out" > "$diff_file"

# Если файл с отличиями не пуст → были изменения
if [ -s "$diff_file" ]; then
    # Отправляем текст изменений
    url=$(cat "$diff_file" | jq -sRr @uri)
    curl -s -X POST "https://api.telegram.org/bot$token/sendMessage?chat_id=$chatid&text=$url" > /dev/null

    # Отправляем скриншот (только при наличии изменений!)
    curl -s -X POST https://api.telegram.org/bot$token/sendDocument \
        -F chat_id=$chatid \
        -F document=@"$screenshot" > /dev/null

    # Обновляем снимок для будущих сравнений
    cat "$out" > "$snapshot"

    echo "$(date): изменения найдены, уведомление отправлено" >> /home/and/parser/monitor.log
else
    echo "$(date): изменений нет" >> /home/and/parser/monitor.log
fi
