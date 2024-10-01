from flask import Blueprint, jsonify, render_template, request
from flask_jwt_extended import current_user, get_jwt_identity, jwt_required
from controllers.auth import role_required
from models.user import User
from config.extensions import db

user = Blueprint('user', __name__)  

def load_user_from_jwt(identity):
    return User.query.get(identity)

@user.route('/home')
@jwt_required()
@role_required('user')
def home():
    current_user_id = get_jwt_identity() 
    user = load_user_from_jwt(current_user_id)

    if user:
            if user.is_blocked:  
                return render_template('blocked.html')
            return render_template('home.html', user=user, show_back_button=False)
    else:
        return jsonify({'error': 'User not found'}), 404