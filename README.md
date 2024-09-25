
# File Management System

This is a Dockerized File Management System built with Flask, FastAPI, PostgreSQL, Redis, Celery, Elasticsearch, and Prometheus for monitoring. It includes document upload, classification, metadata extraction, user management, and admin features.

## Prerequisites

To run this application, you need the following installed on your machine:
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- Git

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Nancy4Hany/File-Management-System.git
cd File-Management-System
```

### 2. Environment Configuration

You need to set up your environment variables for your local machine or production environment.

- Create a `.env` file in the root directory and fill in the following:

#### Sample `.env` File

```bash
# PostgreSQL Database Configurations
DB_HOST=db
DB_PORT=5432
DB_USER=your_postgres_user
DB_PASSWORD=your_postgres_password
DB_NAME=docusecure_project

# Flask App Secret Key
SECRET_KEY=your_secret_key_for_flask

# JWT Settings
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ACCESS_TOKEN_EXPIRES=3600  # in seconds

# Redis (for Celery)
REDIS_URL=redis://redis:6379/0

# FastAPI Service URL (for document classification and metadata extraction)
FASTAPI_SERVICE_URL=http://fastapi-app:8000

# Elasticsearch Config
ELASTICSEARCH_HOST=http://elasticsearch:9200

# Prometheus Metrics
PROMETHEUS_METRICS_URL=/metrics
```

> **Important:** Replace `your_postgres_user`, `your_postgres_password`, `your_secret_key_for_flask`, and `your_jwt_secret_key` with secure values specific to your environment.

### 3. Build and Run the Application with Docker

To start all services (Flask, FastAPI, PostgreSQL, Redis, Elasticsearch, Prometheus, Celery) using Docker Compose, run the following command:

```bash
docker-compose up --build
```

This will build and start the services defined in the `docker-compose.yml` file.

### 4. Accessing the Application

- **Flask App (Main System):**  
  Navigate to [http://localhost:5000](http://localhost:5000) to access the Flask web interface.

- **FastAPI (Classification & Metadata Service):**  
  FastAPI is accessible at [http://localhost:8000](http://localhost:8000).

- **Prometheus Metrics:**  
  Metrics for the services can be viewed at [http://localhost:9090/metrics](http://localhost:9090/metrics).

### 5. Using the Application

#### Admin Credentials
- The first user you create will be a regular user, and you can upgrade a user to an admin by using a command in the Flask shell or any tool (ex. tablePlus).
- To make a user an admin:

  ```bash
  docker-compose exec web flask shell
  ```

- Then run the following Python code:

  ```python
  from models.user import User
  from extensions import db

  user = User.query.filter_by(email='user_email@example.com').first()
  user.role = 'admin'
  db.session.commit()
  ```

- **Signup:** To create a new user, go to the signup page: [http://localhost:5000/signup](http://localhost:5000/signup)
- **Login:** You can log in at: [http://localhost:5000/login](http://localhost:5000/login)

#### Upload a Document
- After logging in, go to [http://localhost:5000/upload](http://localhost:5000/upload) to upload a document.

#### View Documents
- You can view the uploaded documents at [http://localhost:5000/documents](http://localhost:5000/documents).

#### Document Classification
- To classify a document, send a **POST** request to [http://localhost:5000/classify_document](http://localhost:5000/classify_document) with the document ID in the request body.
  
  **Example Request Body**:
  ```json
  {
    "doc_id": 1
  }
  ```

#### Document Metadata Extraction
- To extract metadata for a document, send a **GET** request to:
  ```
  http://localhost:5000/documents/<document_id>/metadata
  ```
  where `<document_id>` is the ID of the document.

#### Logs
- Admins can view system logs at [http://localhost:5000/logs](http://localhost:5000/logs) after logging in as an admin.

#### Admin Panel
- Admins can access the admin panel at [http://localhost:5000/admin](http://localhost:5000/admin).

#### Search Documents
- To search documents, go to [http://localhost:5000/search](http://localhost:5000/search). The search functionality allows you to query document titles, descriptions, and content using Elasticsearch.

<!-- ### 6. Running Tests

You can run the automated tests (using `pytest`) to ensure that everything works as expected. Run the following command inside the container:

```bash
docker-compose exec web pytest
``` -->

### 7. Stopping the Application

To stop and remove the Docker containers, run:

```bash
docker-compose down
```

or remove the Docker containers with volumes if you need to forget previous volumes, run:

```bash
docker-compose down --volumes
```

## Folder Structure

```bash
File-Management-System/
├── app.py                # Main Flask app
├── Dockerfile            # Dockerfile for the Flask app
├── docker-compose.yml    # Docker Compose configuration for all services
├── models/               # Models for users, documents, logs, etc.
├── routes.py             # Flask routes for user management, document handling, etc.
├── templates/            # HTML templates for the frontend
├── tasks.py              # Celery tasks for background processing
├── fastapi_service/      # FastAPI service for document classification & metadata
├── logs/                 # Log files
└── .env                  # Environment variables (should not be committed)
```

## Key Technologies

- **Flask**: Backend framework for handling user authentication, document uploads, and admin features.
- **FastAPI**: Service for document classification and metadata extraction.
- **PostgreSQL**: Database for storing user, document, and log data.
- **Redis**: Used as a message broker for Celery background tasks.
- **Celery**: Asynchronous task queue for processing document classification and metadata in the background.
- **Elasticsearch**: Provides search functionality for documents.
- **Prometheus**: Used for monitoring the system metrics.


