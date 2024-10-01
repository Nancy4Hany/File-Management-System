from werkzeug.security import generate_password_hash
from utils.logging.logger_singleton import SingletonLogger
from models.user import User
from models.document import Document
from config.extensions import db
from utils.logging.logger import log_to_db
from sqlalchemy.exc import SQLAlchemyError

# User Management Functions
logger = SingletonLogger().get_logger()
def add_user(name, email, password, role):
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return False, 'Email already registered.'

    hashed_password = generate_password_hash(password, method='scrypt')
    new_user = User(name=name, email=email, password=hashed_password, role=role)
    db.session.add(new_user)
    db.session.commit()

    log_to_db('ADMIN', f'Admin added a new user: {email}')
    return True, 'User added successfully.'

def edit_user(user_id, name, email, password, role):
    user = User.query.get(user_id)
    if not user:
        return False, 'User not found.'

    user.name = name
    user.email = email
    if password:  
        user.password = generate_password_hash(password, method='scrypt')
    user.role = role
    db.session.commit()

    log_to_db('ADMIN', f'Admin edited user: {email}')
    return True, 'User updated successfully.'

#delete
def delete_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return False, 'User not found.'

        db.session.delete(user)
        db.session.commit()

        log_to_db('ADMIN', f'Admin deleted user: {user.email}')
        return True, 'User deleted successfully.'

    except SQLAlchemyError as e:
        db.session.rollback()  
        logger.error(f"Database error: {e}")
        return False, 'Failed to delete user due to a database error.'

#block 
import redis
from flask_jwt_extended import decode_token
from datetime import timedelta

# Init Redis
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

# Cache expiry time based on token lufetime
TOKEN_EXPIRY = timedelta(hours=1) 

def block_unblock_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return False, 'User not found.'

    user.is_blocked = not user.is_blocked
    db.session.commit()

    action = 'unblocked' if not user.is_blocked else 'blocked'

    # If the user is blocked, revoke all tokens
    if user.is_blocked:
        
        token_jtis = get_user_token_jtis(user)  
        for jti in token_jtis:
            redis_client.setex(jti, TOKEN_EXPIRY, 'revoked')  

    log_to_db('ADMIN', f'Admin {action} user: {user.email}')
    return True, f'User {action} successfully.'

def get_user_token_jtis(user):
    # Placeholder function 
    return []


# Document Management Functions
def mark_document_as_spam(document_id):
    document = Document.query.get(document_id)
    if not document:
        return {'success': False, 'message': 'Document not found.'}

    # Toggle the spam status
    document.is_spam = not document.is_spam
    db.session.commit()

    action = 'unmarked as spam' if not document.is_spam else 'marked as spam'
    log_to_db('ADMIN', f'Admin {action} document: {document.title}')
    return {'success': True, 'message': f'Document {action} successfully.'}