from app import create_app
from config.extensions import make_celery

app = create_app()


celery = make_celery(app)


celery.conf.broker_connection_retry = True
celery.conf.broker_connection_retry_on_startup = True

if __name__ == '__main__':
    celery.start()