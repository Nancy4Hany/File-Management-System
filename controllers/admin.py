from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.user import User
from models.document import Document
from models.logs import Log
from extensions import db
from controllers.auth import role_required
from werkzeug.security import generate_password_hash

admin = Blueprint('admin', __name__)

# View Users
@admin.route('/admin/users', methods=['GET'])
@role_required('admin')
@login_required
def view_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users)

# Add User
@admin.route('/admin/users/add', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def add_user():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role'] 

        new_user = User(name=name, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash(f'User {name} added successfully', 'success')
        return redirect(url_for('admin.view_users'))

    return render_template('admin_add_user.html')

# Edit User
@admin.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form['email']
        user.password = generate_password_hash(request.form['password'])
        user.role = request.form['role']

        db.session.commit()
        flash(f'User {user.name} updated successfully', 'success')
        return redirect(url_for('admin.view_users'))

    return render_template('admin_edit_user.html', user=user)

# Delete User
@admin.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@role_required('admin')
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.name} deleted successfully', 'success')
    return redirect(url_for('admin.view_users'))

# Block/Unblock User
@admin.route('/admin/users/<int:user_id>/block', methods=['POST'])
@role_required('admin')
@login_required
def block_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_blocked = not user.is_blocked
    db.session.commit()
    action = 'blocked' if user.is_blocked else 'unblocked'
    flash(f'User {user.name} {action} successfully', 'success')
    return redirect(url_for('admin.view_users'))

# View Documents
@admin.route('/admin/documents', methods=['GET'])
@role_required('admin')
@login_required
def view_documents():
    documents = Document.query.all()
    return render_template('admin_documents.html', documents=documents)

# Mark/Unmark Spam Document
@admin.route('/admin/documents/<int:doc_id>/spam', methods=['POST'])
@role_required('admin')
@login_required
def spam_document(doc_id):
    document = Document.query.get_or_404(doc_id)
    document.is_spam = not document.is_spam
    db.session.commit()
    action = 'marked as spam' if document.is_spam else 'unmarked as spam'
    flash(f'Document {document.title} {action} successfully', 'success')
    return redirect(url_for('admin.view_documents'))

# View Logs
@admin.route('/admin/logs', methods=['GET'])
@role_required('admin')
@login_required
def view_logs():
    query = request.args.get('query')
    if query:
        logs = Log.query.filter(Log.message.ilike(f'%{query}%')).all()
    else:
        logs = Log.query.all()

    return render_template('admin_logs.html', logs=logs)
