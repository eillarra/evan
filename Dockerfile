FROM python:3.11-slim

EXPOSE 5000

RUN apt-get update && \
  apt-get install -y build-essential default-libmysqlclient-dev && \
  rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -q -r requirements.txt

COPY . /app
