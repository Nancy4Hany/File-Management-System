from abc import ABC, abstractmethod
import textract
from docx import Document as DocxDocument  
class DocumentProcessor(ABC):
    @abstractmethod
    def process(self, document):
        pass

class PDFProcessor(DocumentProcessor):
    def process(self, document):
        print(f"Processing PDF document {document.title}")
        try:
            text = textract.process(document.file_url)
            print(f"Extracted Text: {text[:100]}...")  
        except Exception as e:
            print(f"Error processing PDF: {e}")

class WordProcessor(DocumentProcessor):
    def process(self, document):
        print(f"Processing Word document {document.title}")
        try:
            doc = DocxDocument(document.file_url)
            text = '\n'.join([para.text for para in doc.paragraphs])
            print(f"Extracted Text: {text[:100]}...")
        except Exception as e:
            print(f"Error processing Word document: {e}")

class DocumentProcessorFactory:
    @staticmethod
    def get_processor(file_extension):
        if file_extension == 'pdf':
            return PDFProcessor()
        elif file_extension == 'docx':
            return WordProcessor()
        else:
            raise ValueError('Unsupported file type')
