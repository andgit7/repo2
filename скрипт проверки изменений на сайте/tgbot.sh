#!/bin/bash

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#задание переменных
#курл страницы, выбрать строки, обрезать лишнее > записать в файл index.html
#сравнение изменений в файлах, grand_snapshot.txt и index.html разницу, если она есть записать в zdarova-zaebal.txt
#отправить в ТГ бота файл zdarova-zaebal.txt если он не пустой (пустой не отправится), пустым он будет если не было изменений в файлах выше
#записать содержимое index.html в grand_snapshot.txt (сделать снимок файла для дальнейшего сравнения), пока index.html и grand_snapshot.txt будут равны файл zdarova-zaebal.txt не отправится
#файл отправится в ТГ в случае изменений на сайте
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



chatid=376050665
curl=https://grandtrain.ru/tickets/2078001-2000000/30.06.2025/092%D0%A1/
token=7840513805:AAESfH3LIHUn_50fC5NxclX2d9mvoYJxgpw



curl $curl | grep нижних |  sed -r 's/(.+нижних).+/\1/' | sed 's|.*span>||'  > /var/www/nextcloud/grand/index.html

diff --changed-group-format='%>' --unchanged-group-format='' /home/and/bottg/grand_snapshot.txt /var/www/nextcloud/grand/index.html > /home/and/bottg/zdarova-zaebal.txt

curl -s -X POST https://api.telegram.org/bot$token/sendDocument -F chat_id=$chatid -F document=@"/home/and/bottg/zdarova-zaebal.txt" > /dev/null

cat /var/www/nextcloud/grand/index.html > /home/and/bottg/grand_snapshot.txt

