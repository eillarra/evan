FROM python:3.7-alpine

# install wkhtmltopdf
RUN apk add --no-cache wkhtmltopdf \
        --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing/

WORKDIR /app
COPY requirements.txt /app/

# ensure Alpine Linux includes the necessary packages
RUN apk add --no-cache bash \
        mariadb-connector-c mysql-client \
    && apk add --virtual .build build-base \
        mariadb-connector-c-dev \
    && pip install --no-cache-dir -q -r requirements.txt \
    && apk del .build

COPY . /app

EXPOSE 5000
