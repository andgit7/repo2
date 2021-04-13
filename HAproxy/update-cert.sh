#!/usr/bin/env bash

# Renew the certificate
certbot renew --force-renewal

# Concatenate new cert files, with less output (avoiding the use tee and its output to stdout)
bash -c "cat /etc/letsencrypt/live/virus-cmv.ru/fullchain.pem /etc/letsencrypt/live/virus-cmv.ru/privkey.pem > /etc/ssl/virus-cmv.ru/virus-cmv.ru.pem"
bash -c "cat /etc/letsencrypt/live/virus-hpv.ru/fullchain.pem /etc/letsencrypt/live/virus-hpv.ru/privkey.pem > /etc/ssl/virus-hpv.ru/virus-hpv.ru.pem"
# Reload  HAProxy
service haproxy restart