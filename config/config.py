import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'secretkey')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://userr:docusecure_password@db:5432/docusecure_project')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ACCESS_TOKEN_EXPIRES = 3600  
    JWT_COOKIE_SECURE = True  
    JWT_TOKEN_LOCATION = ['cookies'] 
    WTF_CSRF_ENABLED = False 
    JWT_COOKIE_CSRF_PROTECT = False 
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
    CELERY_BROKER_URL = 'redis://redis:6379/0'
    CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
