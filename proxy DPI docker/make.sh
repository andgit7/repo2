#!/bin/bash


cd /var/dpi/
make
make install
#mkdir /etc/dpi/
#cp /var/dpi/dist/linux/byedpi.service /usr/lib/systemd/system/byedpi.service
#cp /var/dpi/dist/linux/byedpi.conf /usr/lib/systemd/system/byedpi.conf
#service byedpi enable 
#ciadpi --port 1235 --split 1 --disorder 3+s --mod-http=h,d --auto=torst --tlsrec 1+s