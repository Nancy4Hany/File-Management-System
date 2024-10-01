FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    libmagic1 \
    libmagic-dev \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . . 

EXPOSE 8000


ENV DATABASE_URL=postgresql://userr:docusecure_password@db:5432/docusecure_project
ENV AUTHJWT_SECRET_KEY=your-secret-key

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
