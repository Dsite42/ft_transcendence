FROM python:3.10-slim
WORKDIR /app
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN mkdir -p /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/
RUN python manage.py collectstatic --noinput

RUN chmod -R 755 /app/static
RUN chown -R www-data:www-data /app/static

CMD ["sh", "-c", "sleep 20 && python3 manage.py makemigrations && python3 manage.py migrate && python3 manage.py runserver 0.0.0.0:8000"]
