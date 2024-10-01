import os
from flask import current_app, request
import requests
from models.document import Document
from config.extensions import db
from werkzeug.utils import secure_filename
from tasks.tasks import process_document_task
# from services.elasticsearch_service import search_documents_in_es, index_document_es
import logging

logger = logging.getLogger(__name__)


# List documents for the current user
def list_user_documents(user_id):
    return Document.query.filter_by(uploaded_by=user_id).all()

# Upload a document and trigger processing
import tempfile
import shutil
import os

def upload_document(title, description, file, uploaded_by, upload_folder):
    # Creating a temp directory and file
    temp_dir = tempfile.mkdtemp()
    temp_file = tempfile.NamedTemporaryFile(dir=temp_dir)

    file.save(temp_file.name)

    # Process the file

    file_path = os.path.join(upload_folder, secure_filename(file.filename))
    shutil.copy(temp_file.name, file_path)

    shutil.rmtree(temp_dir)
    document = Document(
        title=title,
        description=description,
        file_url=file_path,
        uploaded_by=uploaded_by
    )
    db.session.add(document)
    db.session.commit()

    return document


# Edit a document's title and description
def edit_document(document_id, title, description):
    document = Document.query.get(document_id)
    if document:
        document.title = title
        document.description = description
        db.session.commit()
        return document
    return None

# Delete a document
def delete_document(document_id):
    document = Document.query.get(document_id)
    if document:
        db.session.delete(document)
        db.session.commit()
        return True
    return False

# View a document by ID
def view_document(document_id):
    return Document.query.get_or_404(document_id)


# Search for documents using Elasticsearch
# def search_documents(query):
#     document_ids = search_documents_in_es(query)
#     documents = Document.query.filter(Document.id.in_(document_ids)).all()
    
#     return [
#         {
#             'id': doc.id,
#             'title': doc.title,
#             'description': doc.description,
#             'uploaded_at': doc.uploaded_at,
#             'status': doc.status
#         }
#         for doc in documents
#     ]

# Classify document using Fast..
def classify_document(doc_id, fastapi_url):
    document = Document.query.get(doc_id)
    if not document:
        logger.error(f"Document with ID {doc_id} not found.")
        return None, 'Document not found'
    file_path = os.path.join(current_app.root_path, document.file_url)


    payload = {
        "id": document.id,
        "file_path": document.file_url 
    }

    try:
        headers = {"Authorization": f"Bearer {request.cookies.get('access_token_cookie')}"}

        response = requests.post(f"{fastapi_url}/classify", json=payload, headers=headers)

        if response.status_code == 200:
            return response.json(), None  
        logger.error(f"Classification failed: {response.status_code} {response.text}")
        return None, f"Classification failed: {response.status_code} {response.text}"

    except requests.exceptions.RequestException as e:
        logger.error(f"Error during classification: {e}")
        return None, 'Error connecting to classification service'


# Fetch document metadata using FastAPI
def fetch_document_metadata(document_id, fastapi_url):
    fastapi_url = current_app.config['FASTAPI_SERVICE_URL']
    document = Document.query.get(document_id)
    if not document:
        return None, 'Document not found'

    try:

        headers = {"Authorization": f"Bearer {request.cookies.get('access_token_cookie')}"}

        response = requests.get(f"{fastapi_url}/documents/{document_id}/metadata", headers=headers)

        if response.status_code == 200:
            return response.json()['metadata'], None
        else:
            return None, f"Failed to fetch metadata: {response.status_code} {response.text}"
    except requests.exceptions.RequestException as e:
        return None, f'Error connecting to metadata service: {str(e)}'
