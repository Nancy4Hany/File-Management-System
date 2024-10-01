
FROM python:3.10-slim

RUN useradd -ms /bin/bash celery_user

RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping \
    libpq-dev \
    build-essential \
    libmagic1 \
    file \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .


RUN mkdir -p /app/uploads /usr/src/app/logs && \
    chown -R celery_user:celery_user /app/uploads /usr/src/app/logs


RUN chown -R celery_user:celery_user /app/uploads

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

RUN chown -R celery_user:celery_user /app

USER celery_user

EXPOSE 5000

ENTRYPOINT ["/app/entrypoint.sh"]


CMD ["flask", "run", "--host=0.0.0.0"]