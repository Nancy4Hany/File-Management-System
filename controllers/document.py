from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for, current_app
from flask_login import current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.elasticsearch_service import es
import requests
from models.document import Document
from tasks.tasks import process_document_task
from utils.logging.logger import log_to_db
from services.document_service import (
    list_user_documents, 
    upload_document, 
    edit_document, 
    delete_document, 
    view_document, 
    classify_document, 
)
from controllers.auth import role_required
from wtforms import StringField, FileField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm

document = Blueprint('document', __name__)

class UploadForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = StringField('Description')
    file = FileField('File(s)', validators=[DataRequired()], render_kw={'multiple': True})
    submit = SubmitField('Upload')


# List / search documents for the current user
@document.route('/documents', methods=['GET'])
@jwt_required()  
@role_required('user')  
def list_or_search_documents():
    user_id = get_jwt_identity() 
    query = request.args.get('query', '') 

    print(f"Received query: {query}") 

    if query: 
        try:
            search_results = es.search(index='documents', body={
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title", "description", "content"]
                    }
                }
            })

            
            print(f"Elasticsearch results: {search_results}")

            document_ids = [hit["_id"] for hit in search_results['hits']['hits']]
            documents = Document.query.filter(Document.id.in_(document_ids)).all()

            print(f"Documents found: {documents}")

        except Exception as e:

            print(f"Elasticsearch query failed: {e}")
            return jsonify({"error": "Failed to search documents"}), 500
    else: 
        documents = list_user_documents(user_id)

    if 'text/html' in request.accept_mimetypes: 
        return render_template('view_documents.html', documents=documents)
    else:  
        response_data = [{
            'id': doc.id,
            'title': doc.title,
            'description': doc.description,
            'uploaded_at': doc.uploaded_at.strftime('%Y-%m-%d %H:%M:%S'),
            'status': doc.status
        } for doc in documents]
        return jsonify(response_data)


# Upload a document
@document.route('/upload', methods=['GET', 'POST'])
@jwt_required()
def upload_document_route():
    form = UploadForm()

    if form.validate_on_submit():
        files = request.files.getlist("file")  

        task_ids = [] 
        for file in files:

            document = upload_document(
                title=form.title.data,
                description=form.description.data,
                file=file,
                uploaded_by=get_jwt_identity(),
                upload_folder=current_app.config['UPLOAD_FOLDER']
            )
            
            task = process_document_task.delay(document.id)
            task_ids.append(task.id)  
        
        return jsonify({
            'message': 'Documents uploaded and are being processed',
            'task_ids': task_ids
        }), 200

    return render_template('upload.html', form=form)




# cancel task 
@document.route("/cancel/<task_id>")
def cancel_task(task_id):
    task = process_document_task.AsyncResult(task_id)
    task.revoke(terminate=True)  # Revoke the task
    return jsonify({"message": "Task cancelled!"}), 200


# tracking doc status 
@document.route('/task_status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    task = process_document_task.AsyncResult(task_id)

    response = {
        'task_id': task.id,
        'state': task.state,
        'info': None
    }
    
    try:
        if task.state == 'SUCCESS':
            response['info'] = task.result
        elif task.state == 'FAILURE':
            response['info'] = 'An error occurred while processing the task.'
        else:
            response['info'] = task.info if task.info else 'No information available yet'
    except Exception as e:
        response['info'] = 'Unexpected error occurred while retrieving the task status.'

    return jsonify(response)




# Edit a document
@document.route('/documents/<int:document_id>/edit', methods=['GET', 'POST'])
@jwt_required()  
@role_required('user')
def edit_document_route(document_id):
    user_id = get_jwt_identity()  
    document = view_document(document_id)

    if document.uploaded_by != user_id:
        return jsonify({'error': 'Unauthorized access'}), 403

    if request.method == 'POST':
        data = request.json
        edit_document(document_id, data['title'], data['description'])
        log_to_db('EDIT', f'{user_id} edited the document {document.title}.')
        return jsonify({'success': True})

    # Returning doc details for the modal edit form
    return jsonify({
        'id': document.id,
        'title': document.title,
        'description': document.description
    })


# Delete a document
@document.route('/documents/<int:document_id>/delete', methods=['POST'])
@jwt_required()  
@role_required('user')
def delete_document_route(document_id):
    user_id = get_jwt_identity()  
    document = view_document(document_id)

    if document.uploaded_by != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    delete_document(document_id)
    log_to_db('DELETE', f'{user_id} deleted {document.title}.')
    return jsonify({'success': True})


# View a document
@document.route('/documents/<int:document_id>/view', methods=['GET'])
@jwt_required()  
@role_required('user')
def view_document_route(document_id):
    print(f"View document route called with document_id: {document_id}")
    document = view_document(document_id)
    print(f"Document found: {document}")
    return render_template('view_documents.html', document=document, view_mode=True)

#classify
@document.route('/classify_document/<int:doc_id>', methods=['POST', 'GET'])
@jwt_required()
@role_required('admin')
def classify_document_route(doc_id):
    classification_result = None

    if request.method == 'POST':
        fastapi_url = current_app.config.get('FASTAPI_SERVICE_URL')
        
        if not fastapi_url:
            return jsonify({"error": "FastAPI service URL not configured"}), 500

        result, error = classify_document(doc_id, fastapi_url)

        if error:
            return jsonify({"error": error}), 404

        classification_result = result
    
    return render_template('classify_document.html', document_id=doc_id, classification_result=classification_result)




# Fetch document metadata using external FastAPI service
@document.route('/<int:document_id>/metadata', methods=['GET'])
@jwt_required()  
@role_required('admin')
def fetch_document_metadata_route(document_id):
    fastapi_url = current_app.config['FASTAPI_SERVICE_URL']
    document = Document.query.get(document_id)
    if not document:
        return None, 'Document not found'

    try:

        headers = {"Authorization": f"Bearer {request.cookies.get('access_token_cookie')}"}

        response = requests.get(f"{fastapi_url}/documents/{document_id}/metadata", headers=headers)

        if response.status_code == 200:
            metadata = response.json()['metadata']
            return render_template('view_document.html', document=document, metadata=metadata)
        else:
            return None, f"Failed to fetch metadata: {response.status_code} {response.text}"
    except requests.exceptions.RequestException as e:
        return None, f'Error connecting to metadata service: {str(e)}'