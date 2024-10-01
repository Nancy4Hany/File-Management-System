from werkzeug.security import generate_password_hash
from models.user import User
from config.extensions import db

def create_user(name, email, password):
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return False, 'Email already registered.'

    hashed_password = generate_password_hash(password, method='scrypt')
    user = User(name=name, email=email, password=hashed_password)
    db.session.add(user)
    db.session.commit()
    return True, 'User created successfully.'

def get_user_by_email(email):
    return User.query.filter_by(email=email).first()


