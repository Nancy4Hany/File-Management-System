
import threading
import requests
from extensions import db
from models.document import Document
from logger import log_to_db
from datetime import datetime

def process_document(document_id):
    document = Document.query.get(document_id)
    if not document:
        return

    document.status = "Processing"
    db.session.commit()

    try:
        response = requests.post('https://api.externalservice.com/v1/documents/metadata/extract', json={'file_url': document.file_url})
        response_data = response.json()
        document.title = response_data['extracted_metadata']['title']
        document.status = "Processed"
        document.processed_at = datetime.utcnow()
        
        db.session.commit()
        log_to_db("INFO", f"Document {document.title} processed successfully.")
    except Exception as e:
        document.status = "Failed"
        db.session.commit()
        log_to_db("ERROR", f"Failed to process document {document.id}: {str(e)}")

def async_document_processor(document_id):
    thread = threading.Thread(target=process_document, args=(document_id,))
    thread.start()
