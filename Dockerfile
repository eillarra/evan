FROM python:3.7-alpine

WORKDIR /app
COPY requirements.txt /app/

# ensure Alpine Linux includes the necessary packages
RUN apk add --no-cache bash \
        mariadb-connector-c mysql-client \
        freetype jpeg libpng libwebp lcms2 openjpeg tiff zlib \
    && apk add --virtual .build build-base \
        mariadb-connector-c-dev \
        freetype-dev jpeg-dev libpng-dev libwebp-dev lcms2-dev openjpeg-dev tiff-dev zlib-dev \
    && pip install --no-cache-dir -q -r requirements.txt \
    && apk del .build

COPY . /app

EXPOSE 5000
