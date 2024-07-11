#!/bin/bash
set -e
if [ ! -e /etc/.firstrun ]; then
    python3 manage.py makemigrations
    python3 manage.py migrate
    touch /etc/.firstrun
fi
if [ ! -e /app/staticfiles/.firstrun ]; then
    python3 manage.py collectstatic --noinput
    touch /app/staticfiles/.firstrun
fi
if [ ! -e /certificates/ssl.crt ] || [ ! -e /certificates/ssl.key ]; then
    openssl req -x509 -days 365 -newkey rsa:2048 -nodes -out '/certificates/ssl.crt' -keyout '/certificates/ssl.key' -subj "/CN=$PUBLIC_HOST" -quiet
    touch /certificates/.firstrun
fi
touch /tmp/ready
python3 manage.py runserver 0.0.0.0:8000
