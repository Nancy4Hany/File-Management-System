from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from config.extensions import db, login_manager, migrate, make_celery
from prometheus_flask_exporter import PrometheusMetrics
from flask_cors import CORS
from datetime import timedelta
import os
import logging
import redis

logger = logging.getLogger("flask-app")
logging.basicConfig(level=logging.INFO)

redis_client = redis.StrictRedis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    password=os.getenv('REDIS_PASSWORD', 'supersecurepassword'),
    db=0,
    decode_responses=True
)


TOKEN_EXPIRY = timedelta(hours=1)


from routes import register_routes

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'secretkey')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://userr:docusecure_password@db:5432/docusecure_project')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_COOKIE_SECURE'] = False 
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']  
    app.config['WTF_CSRF_ENABLED'] = False  
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False
    app.config['UPLOAD_FOLDER'] = '/app/uploads'  
    app.config['FASTAPI_SERVICE_URL'] = os.getenv('FASTAPI_SERVICE_URL', 'http://fastapi-app:8000')
    app.config['JWT_COOKIE_SAMESITE'] = 'None'
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  


    app.config['REDIS_PASSWORD'] = os.getenv('REDIS_PASSWORD', 'supersecurepassword')
    app.config['REDIS_HOST'] = os.getenv('REDIS_HOST', 'redis')
    app.config['REDIS_PORT'] = int(os.getenv('REDIS_PORT', 6379))

  
    app.config.update(
        CELERY_BROKER_URL=f'redis://:{app.config["REDIS_PASSWORD"]}@{app.config["REDIS_HOST"]}:{app.config["REDIS_PORT"]}/0',
        result_backend=f'redis://:{app.config["REDIS_PASSWORD"]}@{app.config["REDIS_HOST"]}:{app.config["REDIS_PORT"]}/0'
    )

    logger.info(f"Redis connection details: Host={app.config['REDIS_HOST']}, Port={app.config['REDIS_PORT']}, Password={'******' if app.config['REDIS_PASSWORD'] else 'None'}")

 
    jwt_manager = JWTManager(app)


    CORS(app, supports_credentials=True)


    metrics = PrometheusMetrics(app)


    register_extensions(app)


    register_routes(app)

    celery = make_celery(app)
    app.celery = celery  


    @jwt_manager.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        jti = jwt_payload['jti']
        entry = redis_client.get(jti)
        return entry == 'revoked'


    @app.errorhandler(401)
    def handle_revoked_token(e):
        return jsonify({
            "message": "Access denied. Your token has been revoked."
        }), 401

    return app

def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)