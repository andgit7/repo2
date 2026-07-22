#!/bin/bash

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Переменные
chatid=376050665
result=/home/and/pars5/snapshot/result.txt
token=7840513805:AAESfH3LIHUn_50fC5NxclX2d9mvoYJxgpw
diff_file=/home/and/pars5/snapshot/diff.txt
snapshot=/home/and/pars5/snapshot/grand_snapshot.txt
out=/home/and/pars5/snapshot/out.txt
screenshot=/home/and/pars5/snapshot/screenshot.png
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Извлечение нужных строк из index.html
#sed -rn 's/.*span>([^<]*(нижних|нижнее)[^<]*).*/\1/p' "$path" > "$out"
grep "Плацкарт: нижних" "$result" > "$out"

# Сравнение с предыдущим снимком, запись отличий в diff_file
awk 'NR==FNR {old[NR]=$0; next} $0 > old[FNR]' "$snapshot" "$out" > "$diff_file"

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
    #cat "$out" > "$snapshot"

    echo "********************************************************************************************************" >> /home/and/pars5/snapshot/monitor.log
    echo "$(date): изменения найдены, уведомление отправлено. Последние значения парсера: $(cat "$out" | tr '\n' ' ')" >> /home/and/pars5/snapshot/monitor.log
    echo "********************************************************************************************************" >> /home/and/pars5/snapshot/monitor.log
else
    echo "--------------------------------------------------------------------------------------------------------" >> /home/and/pars5/snapshot/monitor.log
    echo "$(date): изменений нет. Последние значения парсера: $(cat "$out" | tr '\n' ' ')" >> /home/and/pars5/snapshot/monitor.log
    echo "--------------------------------------------------------------------------------------------------------" >> /home/and/pars5/snapshot/monitor.log
fi

cat "$out" > "$snapshot"