from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from celery import Celery

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=f"redis://:{app.config['REDIS_PASSWORD']}@{app.config['REDIS_HOST']}:{app.config['REDIS_PORT']}/0",
        backend=f"redis://:{app.config['REDIS_PASSWORD']}@{app.config['REDIS_HOST']}:{app.config['REDIS_PORT']}/0"
    )
    celery.conf.update(app.config)
    return celery