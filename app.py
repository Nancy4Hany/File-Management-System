from flask import Flask
from flask_jwt_extended import JWTManager
from extensions import db, login_manager, migrate
from routes import main  # Import blueprint here
from prometheus_flask_exporter import PrometheusMetrics
from flask_cors import CORS
from celery_app import make_celery
from datetime import timedelta
import os

def create_app():
    app = Flask(__name__)

   
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'secretkey')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://userr:docusecure_password@db:5432/docusecure_project'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_COOKIE_SECURE'] = True  
    app.config['JWT_TOKEN_LOCATION'] = ['cookies'] 
    app.config['WTF_CSRF_ENABLED'] = False 
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False 
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
    jwt_manager = JWTManager(app)
    # jwt_manager.token_in_cookies = True

    # Enable CORS for all domains
    # CORS(app, supports_credentials=True)  

    app.config.update(
        CELERY_BROKER_URL='redis://redis:6379/0',
        CELERY_RESULT_BACKEND='redis://redis:6379/0'
    )

    metrics = PrometheusMetrics(app)


    register_extensions(app)
    register_resources(app)


    celery = make_celery(app)  
    app.celery = celery 

    return app

def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

def register_resources(app):
    app.register_blueprint(main)  # Register the main blueprint

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
