FROM ubuntu

ENV NGINX_CONF_DIR=/etc/nginx

COPY ./supervisord.conf /etc/supervisor/conf.d/
COPY ./index.php /var/www/html/index.php


RUN   \
        apt -y update \
      && apt -y install nginx \
      && apt -y install php-fpm \ 
      && apt -y install supervisor 
      
      
COPY ./default /etc/nginx/sites-available/default  
COPY ./supervisord.conf /etc/supervisor/conf.d/

EXPOSE 80

CMD ["/usr/bin/supervisord"]  