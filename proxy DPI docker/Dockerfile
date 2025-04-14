FROM ubuntu


ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt -y update 
RUN apt -y install make
RUN apt -y install gcc

COPY ./byedpi-main/ /var/dpi
COPY ./make.sh /etc/dpi/make.sh

COPY ./byedpi-main/dist/linux/byedpi.service /usr/lib/systemd/system/byedpi.service
COPY ./byedpi-main/dist/linux/byedpi.conf /usr/lib/systemd/system/byedpi.conf

RUN /etc/dpi/make.sh


CMD ciadpi --port 1235  --oob 1 --ttl 2 --disorder 1



EXPOSE 1235
