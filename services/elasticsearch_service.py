from elasticsearch import Elasticsearch
import textract
import logging

from models.document import Document
es = Elasticsearch(hosts=["http://elasticsearch:9200"])

logger = logging.getLogger(__name__)

# Create the index 
# def create_index_if_not_exists():
#     if not es.indices.exists(index="documents"):
#         es.indices.create(index="documents", body={
#             "mappings": {
#                 "properties": {
#                     "title": {"type": "text"},
#                     "description": {"type": "text"},
#                     "content": {"type": "text"},
#                     "uploaded_at": {"type": "date"}
#                 }
#             }
#         })

# # Index a document 
# def index_document_es(document):
#     create_index_if_not_exists() 
#     es.index(index='documents', id=document.id, body={
#         'title': document.title,
#         'description': document.description,
#         'content': extract_content(document.file_url),
#         'uploaded_at': document.uploaded_at.isoformat()
#     })

# # Extract content from a document file for indexing
# def extract_content(file_path):
#     try:
#         content = textract.process(file_path).decode('utf-8')
#     except Exception as e:
#         logger.error(f"Error extracting content from {file_path}: {e}")
#         content = 'No content extracted'
    
#     return content

# # Search for documents in Elasticsearch
# # Search for documents in Elasticsearch
# def search_documents_in_es(query):
#     try:
#         search_results = es.search(index='documents', body={
#             "query": {
#                 "multi_match": {
#                     "query": query,
#                     "fields": ["title", "description", "content"]
#                 }
#             }
#         })
#         document_ids = [hit["_id"] for hit in search_results['hits']['hits']]
#         return Document.query.filter(Document.id.in_(document_ids)).all()
#     except Exception as e:
#         logger.error(f"Error searching documents in Elasticsearch: {e}")
#         return []
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
    