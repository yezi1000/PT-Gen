FROM tiangolo/meinheld-gunicorn-flask:python3.7-alpine3.8

LABEL maintainer "BFDZ <root@bfdz.ink>"

COPY ../ /app

COPY ./crontab /etc/crontabs/

COPY ./prestart.sh /app

RUN apk add python3-dev libxml2-dev libxslt-dev zlib-dev gcc libc-dev

RUN pip3 install --no-cache-dir -r requirement.txt
