FROM balenalib/rpi-raspbian:latest
ENV TZ America/Los_Angeles

RUN apt-get update
RUN apt-get -y install libraspberrypi0
RUN apt-get -y install git python3 python3-pip python3-serial python3-pygame rpi.gpio python3-gpiozero python3-rpi.gpio python3-rpi.gpio-dbgsym gpsd chrony supervisor

RUN pip3 install obd gpsd-py3

RUN git clone https://github.com/tmkdev/gentex_magicmirror.git /root/gentex_magicmirror
RUN echo "refclock SHM 0 offset 0.5 delay 0.2 refid NMEA" >> /etc/chrony/chrony.conf

RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord"]