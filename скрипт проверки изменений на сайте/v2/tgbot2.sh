#!/bin/bash

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#задание переменных
#курл страницы, выбрать строки, обрезать лишнее > записать в файл index.html
#сравнение изменений в файлах, grand_snapshot.txt и index.html разницу, если она есть записать в zdarova-zaebal.txt
#отправить в ТГ бота файл zdarova-zaebal.txt если он не пустой (пустой не отправится), пустым он будет если не было изменений в файлах выше
#записать содержимое index.html в grand_snapshot.txt (сделать снимок файла для дальнейшего сравнения), пока index.html и grand_snapshot.txt будут равны файл zdarova-zaebal.txt не отправится
#файл отправится в ТГ в случае изменений на сайте
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



chatid=blabla
path=/home/and/parser/parsed_grandtrain_ru/index.html
token=blabla
file=/home/and/parser/zdarova-zaebal.txt
#url=$(cat "$file" | jq -sRr @uri)

#sed -rn 's/.*span>([^<]*(нижних|верхних|верхнее|нижнее)[^<]*).*/\1/p' "$path"  > /home/and/parser/parsed_grandtrain_ru/out.html
sed -rn 's/.*span>([^<]*(нижних|нижнее)[^<]*).*/\1/p' "$path"  > /home/and/parser/parsed_grandtrain_ru/out.html
diff --changed-group-format='%>' --unchanged-group-format='' /home/and/parser/grand_snapshot.txt /home/and/parser/parsed_grandtrain_ru/out.html > /home/and/parser/zdarova-zaebal.txt

url=$(cat "$file" | jq -sRr @uri) #переменная задаётся непосредствено перед отправкой сообщения в ТГ

curl -s -X POST "https://api.telegram.org/bot$token/sendMessage?chat_id=$chatid&text=$url" > /dev/null

#curl -s -X POST https://api.telegram.org/bot$token/sendDocument -F chat_id=$chatid -F document=@"/home/and/parser/zdarova-zaebal.txt" > /dev/null


cat /home/and/parser/parsed_grandtrain_ru/out.html > /home/and/parser/grand_snapshot.txt



