import logging
from flask import current_app
from celery import shared_task
from document_factory import DocumentProcessorFactory
from extensions import db
from models.document import Document

@shared_task
def process_document_task(document_id):
    with current_app.app_context():  # Ensure that the app context is available
        document = Document.query.get(document_id)
        if document:
            try:
                # Get the file extension and use the factory to get the correct processor
                file_extension = document.file_url.rsplit('.', 1)[1].lower()
                processor = DocumentProcessorFactory.get_processor(file_extension)

                # Process the document
                processor.process(document)
                
                # Mark the document as completed
                document.status = 'completed'
            except Exception as e:
                document.status = 'failed'
                logging.error(f"Error processing document {document_id}: {e}")
            finally:
                db.session.commit()
