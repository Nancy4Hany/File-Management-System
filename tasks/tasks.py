import logging
import time
from celery import shared_task
from models.document import Document
from config.extensions import db


logger = logging.getLogger(__name__)

@shared_task(bind=True)
def process_document_task(self, document_id):
    from app import create_app
    
    app = create_app()
    
    with app.app_context():

        logger.info(f"Starting processing for document ID {document_id}")
        
        document = Document.query.get(document_id)
        if not document:

            logger.error(f"Document {document_id} not found")
            self.update_state(state='FAILURE', meta={'error': 'Document not found'})
            return "Document not found"


        for i in range(5):
            logger.info(f"Processing step {i+1} for document {document.title}")
            time.sleep(1) 
            self.update_state(state='PROGRESS', meta={'step': i + 1})


        document.is_processed = True
        document.status = 'Processed'
        db.session.commit()

        logger.info(f"Document {document.title} processed successfully")
        return f"Document {document.title} processed successfully"
