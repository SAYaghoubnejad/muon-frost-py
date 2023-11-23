FROM python:3.10-alpine

WORKDIR /app

COPY ./requirements.txt .


RUN apk add --no-cache git gmp-dev build-base pkgconfig && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 5017

ENV PYTHONPATH="./:$PYTHONPATH"


RUN apk del build-base && \
    rm -rf /var/cache/apk/* /root/.cache


RUN find /app -name "*.pyc" -exec rm -f {} \;


COPY . .
COPY ./common/node_docker_dns.py ./common/dns.py