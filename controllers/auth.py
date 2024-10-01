from functools import wraps
from fastapi import logger
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, set_access_cookies, unset_jwt_cookies
from werkzeug.security import check_password_hash
from models.user import User
from services.user_service import create_user, get_user_by_email
import logging
from config.extensions import login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

auth = Blueprint('auth', __name__)

from functools import wraps

logger = logging.getLogger("DocuSecureLogger")

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            current_user = User.query.get(current_user_id)

            if not current_user:
                logger.warning("User not found.")
                return jsonify({"msg": "User not found"}), 404

            logger.info(f"User {current_user.email} is trying to access admin features.")

            # Check if the user has the correct role
            if current_user.role != role:
                logger.warning(f"Access denied for user {current_user.email}. {role.capitalize()} role required.")
                return jsonify({"msg": f"Access denied. {role.capitalize()} role required."}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Login Route

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        print("Login request received")
        email = request.json.get('email') if request.is_json else request.form.get('email')
        password = request.json.get('password') if request.is_json else request.form.get('password')
        print(f"Login attempt for email: {email}")

        user = get_user_by_email(email)

        if user:
            print("User found, checking password")
            if check_password_hash(user.password, password):
                print("Password correct, creating JWT token")
                token = create_access_token(identity=user.id)
                response = jsonify({'message': 'Login successful', 'token': token})

                if user.role == 'admin':
                    redirect_url = url_for('admin.admin_panel')  
                elif user.role == 'user':
                    redirect_url = url_for('user.home')  
                else:

                    redirect_url = url_for('auth.login')

                response = jsonify({'message': 'Login successful', 'token': token, 'redirect_url': redirect_url})
                set_access_cookies(response, token, max_age=3600)  # Set JWT cookies
                return response
            else:
                print("Password incorrect")
                return jsonify({'error': 'Invalid email or password'}), 401
        else:
            print("User not found")
            return jsonify({'error': 'Invalid email or password'}), 401

    return render_template('login.html')



# Signup Route
@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            name = data.get('name')
            email = data.get('email')
            password = data.get('password')
        else:
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')

        result, message = create_user(name, email, password)

        if not result:
            return jsonify({'message': message}), 400 if request.is_json else render_template('signup.html', error=message)

        if request.is_json:
            return jsonify({'message': 'Signup successful. Please log in.'}), 201
        else:
            flash('Signup successful, please log in', 'success')
            return redirect(url_for('auth.login'))

    return render_template('signup.html')


# Token Refresh Route
@auth.route('/refresh-token', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    current_user_id = get_jwt_identity()
    new_token = create_access_token(identity=current_user_id)
    return jsonify({'token': new_token})


# Logout Route
@auth.route('/logout')
@jwt_required()
def logout():
    response = jsonify({'message': 'Logout successful'})
    unset_jwt_cookies(response)  
    flash('You have been logged out.', 'success')
    return response
