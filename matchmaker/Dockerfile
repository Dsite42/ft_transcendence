FROM python:3.12-alpine
WORKDIR /app
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apk update && \
    apk add --no-cache gcc musl-dev && \
    mkdir -p /app/matchmaker
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/matchmaker/
CMD ["python", "-m", "matchmaker.matchmaker_service"]
