FROM python:3.10-slim
WORKDIR /app
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

COPY container.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/container.sh

RUN mkdir -p /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/
ENTRYPOINT ["container.sh"]
