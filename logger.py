import logging
from extensions import db
from models.logs import Log

log_level_mapping = {
    'UPLOAD': 'INFO',
    'EDIT': 'INFO',
    'DELETE': 'WARNING',
    'VIEW': 'INFO',
}

def log_to_db(level, message):

    log_entry = Log(level=level[:10], message=message)
    db.session.add(log_entry)
    db.session.commit()
    logging_level = log_level_mapping.get(level.upper(), 'INFO')
    logging.log(getattr(logging, logging_level), message)
