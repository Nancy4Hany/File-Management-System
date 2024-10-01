from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required
from utils.logging.logger_singleton import SingletonLogger
from models.user import User
from models.logs import Log
from controllers.auth import role_required
from services.admin_service import add_user, edit_user, delete_user, block_unblock_user, mark_document_as_spam
from models.document import Document
from sqlalchemy.exc import SQLAlchemyError

admin = Blueprint('admin', __name__)

logger = SingletonLogger().get_logger()



@admin.route('/', methods=['GET'])
@jwt_required()
@role_required('admin')
def admin_panel():
    try:
        return render_template('admin_dashboard.html')
    except Exception as e:
        logger.error(f"Error rendering admin dashboard: {str(e)}")  # Log the error message
        return jsonify({"error": "An error occurred while rendering the dashboard.", "details": str(e)}), 500




# View Users
@admin.route('/users', methods=['GET'])
@jwt_required()
@role_required('admin')
def admin_view_users():
    try:
        users = User.query.all()
        return render_template('admin_users.html', users=users)
    except SQLAlchemyError as e:
        logger.error(f"Error fetching users: {e}")
        return jsonify({"msg": "Error fetching users"}), 500
    except Exception as e:
        logger.error(f"Unexpected error fetching users: {e}")
        return jsonify({"error": str(e)}), 500

# Add User
@admin.route('/users/add', methods=['GET', 'POST'])
@jwt_required()
@role_required('admin')
def admin_add_user():
    if request.method == 'POST':
        try:
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']
            role = request.form['role']

            result, message = add_user(name, email, password, role)
            if result:
                flash('User added successfully.', 'success')
            else:
                flash(message, 'danger')

            return redirect(url_for('admin.admin_view_users'))
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            flash("An error occurred while adding the user.", 'danger')
            return redirect(url_for('admin.admin_view_users'))

    return render_template('admin_add_user.html')

# Edit User
@admin.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@jwt_required()
@role_required('admin')
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        try:
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']
            role = request.form['role']

            result, message = edit_user(user_id, name, email, password, role)
            if result:
                flash('User updated successfully.', 'success')
            else:
                flash(message, 'danger')

            return redirect(url_for('admin.admin_view_users'))
        except Exception as e:
            logger.error(f"Error editing user: {e}")
            flash("An error occurred while editing the user.", 'danger')
            return redirect(url_for('admin.admin_view_users'))

    return render_template('admin_edit_user.html', user=user)

# Block/Unblock User
@admin.route('/users/<int:user_id>/block', methods=['POST'])
@jwt_required()
@role_required('admin')
def admin_block_user(user_id):
    try:
        result, message = block_unblock_user(user_id)
        flash(message, 'success' if result else 'danger')
    except Exception as e:
        logger.error(f"Error blocking/unblocking user: {e}")
        flash("An error occurred while processing your request.", 'danger')
    return redirect(url_for('admin.admin_view_users'))

# Delete User
@admin.route('/users/<int:user_id>/delete', methods=['POST'])
@jwt_required()
@role_required('admin')
def admin_delete_user(user_id):
    try:
        result, message = delete_user(user_id)  
        flash(message, 'success' if result else 'danger')
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        flash("An error occurred while deleting the user.", 'danger')
    return redirect(url_for('admin.admin_view_users'))

# View Documents
@admin.route('/documents', methods=['GET'])
@jwt_required()
@role_required('admin')
def admin_view_documents():
    try:
        documents = Document.query.all()
        return render_template('admin_documents.html', documents=documents)
    except SQLAlchemyError as e:
        logger.error(f"Error fetching documents: {e}")
        return jsonify({"msg": "Error fetching documents"}), 500
    except Exception as e:
        logger.error(f"Unexpected error fetching documents: {e}")
        return jsonify({"error": str(e)}), 500

# Mark Document as Spam
@admin.route('/documents/<int:document_id>/spam', methods=['POST'])
@jwt_required()
@role_required('admin')
def admin_spam_document(document_id):
    try:
        result = mark_document_as_spam(document_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error marking document as spam: {e}")
        return jsonify({"success": False, "message": "An error occurred while processing your request."})

# Logs Route
@admin.route('/logs', methods=['GET'])
@jwt_required()
@role_required('admin')
def view_logs():
    query = request.args.get('query')
    try:
        if query:
            logs = Log.query.filter(Log.message.ilike(f'%{query}%')).all()
        else:
            logs = Log.query.all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching logs: {e}")
        return jsonify({"msg": "Error fetching logs"}), 500
    except Exception as e:
        logger.error(f"Unexpected error fetching logs: {e}")
        return jsonify({"error": str(e)}), 500

    return render_template('admin_logs.html', logs=logs)
