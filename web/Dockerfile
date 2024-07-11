FROM python:3.12-alpine
WORKDIR /app
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apk update && apk add bash openssl

COPY container.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/container.sh

RUN mkdir -p /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/
ENTRYPOINT ["container.sh"]
