from datetime import datetime, timedelta
from functools import wraps
import logging
import os
from elasticsearch import Elasticsearch
from flask import Blueprint, app, current_app, g, jsonify, make_response, render_template, redirect, session, url_for, request, flash
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, set_access_cookies, unset_jwt_cookies
from flask_login import login_user, logout_user, login_required, current_user
import jwt
import magic
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from controllers.auth import role_required
# from document_factory import DocumentProcessorFactory
from logger_singleton import SingletonLogger
from models.logs import Log
from models.user import User
from models.document import Document
from extensions import db, login_manager
from logger import log_to_db
import textract
from cryptography.fernet import Fernet

from tasks import process_document_task

main = Blueprint('main', __name__)
FASTAPI_SERVICE_URL = "http://fastapi-app:8000"
es = Elasticsearch(hosts=["http://elasticsearch:9200"])
logger = SingletonLogger().get_logger()

def index_document_es(document):
    es.index(index='documents', id=document.id, body={
        'title': document.title,
        'description': document.description,
        'content': extract_content(document.file_url),
        'uploaded_at': document.uploaded_at.isoformat()
    })
    
def extract_content(file_path):
    try:
        content = textract.process(file_path).decode('utf-8')
    except Exception as e:
        logging.error(f"Error extracting content from {file_path}: {e}")
        content = ''
    
    return content   

def load_or_generate_key():
    key_file = 'secret.key'
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(key)
        return key
  
 
def encrypt_file_data(file_data):
    key = load_or_generate_key()
    cipher = Fernet(key)
    encrypted_data = cipher.encrypt(file_data)
    return encrypted_data


def decrypt_file_data(encrypted_data):
    key = load_or_generate_key()
    cipher = Fernet(key)
    decrypted_data = cipher.decrypt(encrypted_data)
    return decrypted_data    


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('main.login'))
            if current_user.is_blocked:
                return render_template('blocked.html')
            if current_user.role != role:
                flash('You do not have access to this page.', 'danger')
                return redirect(url_for('main.home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.json.get('email') if request.is_json else request.form.get('email')
        password = request.json.get('password') if request.is_json else request.form.get('password')

        
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            token = create_access_token(identity=user.id)
            
            response = jsonify({'message': 'Login successful', 'token': token})
            set_access_cookies(response, token, max_age=3600)  
            
            return response
        else:
            return jsonify({'error': 'Invalid email or password'}), 401

    return render_template('login.html')




def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            token = auth_header.split(" ")[1] if auth_header.startswith("Bearer ") else None

        if not token:
            logging.error("Token is missing!")
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['scrypt'])
            current_user = User.query.get(data['user_id'])
        except jwt.ExpiredSignatureError:
            logging.error("Token expired!")
            return jsonify({'message': 'Token expired!'}), 401
        except jwt.InvalidTokenError:
            logging.error("Invalid token!")
            return jsonify({'message': 'Invalid token!'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

### Signup Route ###
@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        
        if request.is_json:
            data = request.get_json() 
            name = data.get('name')
            email = data.get('email')
            password = generate_password_hash(data.get('password'), method='scrypt')
        else:
            
            name = request.form['name']
            email = request.form['email']
            password = generate_password_hash(request.form['password'], method='scrypt')

        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            if request.is_json:
                return jsonify({'message': 'Email already registered. Please log in.'}), 400
            else:
                flash('Email already registered. Please log in.', 'danger')
                return redirect(url_for('main.login'))

       
        user = User(name=name, email=email, password=password)
        db.session.add(user)
        db.session.commit()

        if request.is_json:
            return jsonify({'message': 'Signup successful. Please log in.'}), 201
        else:
            flash('Signup successful, please log in', 'success')
            return redirect(url_for('main.login'))

    return render_template('signup.html')


@main.route('/logout')
def logout():
    response = make_response(redirect(url_for('main.login')))
    unset_jwt_cookies(response)
    flash('You have been logged out.', 'success')
    return response

### Token Refresh Route ###
@main.route('/refresh-token', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    current_user = get_jwt_identity()
    new_token = create_access_token(identity=current_user, expires_delta=timedelta(hours=1))
    return jsonify({'token': new_token}), 200


### Admin Route ###

@main.route('/admin')
@role_required('admin')
def admin_panel():
    return render_template('admin_dashboard.html')


### user Home Route ###

@main.route('/home')
@jwt_required()  
def home():
    current_user_id = get_jwt_identity() 
    user = User.query.get(current_user_id)
    
    if user:
        return render_template('home.html', user=user)
    else:
        return jsonify({'error': 'User not found'}), 404



@main.route('/documents', methods=['GET'])
@jwt_required()  
def list_documents():
    current_user_id = get_jwt_identity()
    documents = Document.query.filter_by(uploaded_by=current_user_id).all()

    return jsonify([{
        'id': doc.id,
        'title': doc.title,
        'description': doc.description,
        'uploaded_at': doc.uploaded_at,
        'status': doc.status
    } for doc in documents])


from flask_wtf import FlaskForm
from wtforms import StringField, FileField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename

class UploadForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    file = FileField('File', validators=[DataRequired()])
    submit = SubmitField('Upload')

@main.route('/upload', methods=['GET', 'POST'])
@jwt_required()
def upload_document():
    form = UploadForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            file = form.file.data
            filename = secure_filename(file.filename)
            
           
            upload_folder = current_app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
      
            document = Document(
                title=form.title.data,
                description=form.description.data,
                file_url=file_path,
                uploaded_by=get_jwt_identity()  
            )
            db.session.add(document)
            db.session.commit()

            
            process_document_task.delay(document.id)

            return jsonify({'message': 'Document uploaded successfully and is being processed!'}), 200

    return render_template('upload.html', form=form)


@main.route('/documents/<int:document_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('user')
def edit_document(document_id):
    document = Document.query.get_or_404(document_id)

    if document.uploaded_by != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('main.list_documents'))

    if request.method == 'POST':
        document.title = request.form['title']
        document.description = request.form['description']
        db.session.commit()

        log_to_db('EDIT', f'{current_user.email} edited the document {document.title}.')
        flash('Document updated successfully!', 'success')
        return redirect(url_for('main.list_documents'))

    return render_template('edit_document.html', document=document)


@main.route('/documents/<int:document_id>/delete', methods=['POST'])
@login_required
@role_required('user')
def delete_document(document_id):
    document = Document.query.get_or_404(document_id)

    if document.uploaded_by != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('main.list_documents'))

    db.session.delete(document)
    db.session.commit()

    log_to_db('DELETE', f'{current_user.email} deleted {document.title}.')
    flash('Document deleted successfully!', 'success')

    return redirect(url_for('main.list_documents'))


@main.route('/documents/<int:document_id>/view', methods=['GET'])
@login_required
@role_required('user')
def view_document(document_id):
    document = Document.query.get_or_404(document_id)
    return render_template('view_document.html', document=document)


### Logs Route ###
@main.route('/logs')
@role_required('admin')
def view_logs():
    logs = Log.query.all()
    return render_template('logs.html', logs=logs)


### Search Route ###
@role_required('user')
@main.route('/search', methods=['GET', 'POST'])
@login_required
def search_documents():
    query = request.args.get('query')
    documents = []

    if query:
        search_results = es.search(index='documents', body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title", "description", "content"]
                }
            }
        })

        document_ids = [hit["_id"] for hit in search_results['hits']['hits']]
        documents = Document.query.filter(Document.id.in_(document_ids)).all()

    return render_template('search_results.html', documents=documents, query=query)


import logging

logging.basicConfig(level=logging.INFO)


### Classification Route ###

@main.route('/classify_document', methods=['POST'])
def classify_document():
    doc_id = request.json.get("doc_id")
    document = Document.query.get(doc_id)

    if not document:
        return jsonify({"error": "Document not found"}), 404

    response = requests.post(f"{FASTAPI_SERVICE_URL}/classify", json={
        "id": document.id,
        "file_path": document.file_url
    })

    if response.status_code == 200:
        classification_data = response.json()
        return jsonify(classification_data)
    else:
        return jsonify({"error": "Classification failed"}), response.status_code


### Metadata Route ###

@main.route('/documents/<int:document_id>/metadata', methods=['GET'])
@login_required
def fetch_document_metadata(document_id):
    document = Document.query.get_or_404(document_id)

    try:
        response = requests.get(f"{FASTAPI_SERVICE_URL}/documents/{document_id}/metadata")

        if response.status_code == 200:
            metadata = response.json()['metadata']
            return render_template('view_document.html', document=document, metadata=metadata)
        else:
            flash('Failed to fetch document metadata.', 'danger')
            return redirect(url_for('main.view_document', document_id=document_id))

    except requests.exceptions.RequestException as e:
        flash('Error connecting to metadata service.', 'danger')
        return redirect(url_for('main.view_document', document_id=document_id))


    
    
@main.route('/admin/users', methods=['GET'])
@role_required('admin')
def admin_view_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users)


@main.route('/admin/user/add', methods=['GET', 'POST'])
@role_required('admin')
def admin_add_user():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='scrypt')
        role = request.form['role']

        # Create a new user
        new_user = User(name=name, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()

        log_to_db('ADMIN', f'Admin {current_user.email} added a new user: {email}')
        flash('User added successfully.', 'success')
        return redirect(url_for('main.admin_view_users'))
    return render_template('admin_add_user.html')


@main.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form['email']
        user.password = generate_password_hash(request.form['password'], method='scrypt')
        user.role = request.form['role']

        db.session.commit()

        log_to_db('ADMIN', f'Admin {current_user.email} edited user: {user.email}')
        flash('User updated successfully.', 'success')
        return redirect(url_for('main.admin_view_users'))
    
    return render_template('admin_edit_user.html', user=user)


@main.route('/admin/user/<int:user_id>/block', methods=['POST'])
@role_required('admin')
def admin_block_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.role == 'admin':
        flash(f"Cannot block an admin user.", 'danger')
        return redirect(url_for('main.admin_view_users'))

    user.is_blocked = not user.is_blocked  

    db.session.commit()
    log_to_db('ADMIN', f'Admin {current_user.email} {"unblocked" if not user.is_blocked else "blocked"} user: {user.email}')
    flash(f'User {user.email} has been {"unblocked" if not user.is_blocked else "blocked"}.', 'success')

    return redirect(url_for('main.admin_view_users'))



@main.route('/admin/documents', methods=['GET'])
@role_required('admin')
def admin_view_documents():
    documents = Document.query.all()
    return render_template('admin_documents.html', documents=documents)


@main.route('/admin/document/<int:document_id>/spam', methods=['POST'])
@role_required('admin')
def admin_spam_document(document_id):
    document = Document.query.get_or_404(document_id)
    document.is_spam = True  

    db.session.commit()
    log_to_db('ADMIN', f'Admin {current_user.email} marked document as spam: {document.title}')
    flash(f'Document {document.title} has been marked as spam.', 'success')
    
    return redirect(url_for('main.admin_view_documents'))

@main.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@role_required('admin')
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Delete the user from the database
    db.session.delete(user)
    db.session.commit()
    
    log_to_db('ADMIN', f'Admin {current_user.email} deleted user: {user.email}')
    flash(f'User {user.email} has been deleted.', 'success')
    
    return redirect(url_for('main.admin_view_users'))

