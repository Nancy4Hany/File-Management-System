from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from celery import Celery

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def make_celery(app):
    celery = Celery(
        app.import_name,
        broker='redis://redis:6379/0',
        backend='redis://redis:6379/0'
    )
    celery.conf.update(app.config)
    return celery
