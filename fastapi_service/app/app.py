import magic  
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from .models import Base, Document
import os
import time
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()


Instrumentator().instrument(app).expose(app, endpoint="/metrics")

@app.get("/")
def read_root():
    return {"Hello": "World"}

Base.metadata.create_all(bind=engine)

class DocumentRequest(BaseModel):
    id: int  
    file_path: str 

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def classify_content(file_path: str):
    _, ext = os.path.splitext(file_path)
    
    if ext == ".txt":
        return "text file"
    
    mime = magic.Magic(mime=True) 
    mime_type = mime.from_file(file_path)
    
    if "text" in mime_type:
        return "text file"
    elif "pdf" in mime_type:
        return "PDF document"
    elif "image" in mime_type:
        return "image file"
    else:
        return "binary file"

@app.post("/classify")
def classify_document(doc: DocumentRequest, db: Session = Depends(get_db)):
    try:
        with open(doc.file_path, 'rb') as file:
            pass  
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")

    classification_type = classify_content(doc.file_path)

    # Update document classification in the database
    document = db.query(Document).filter(Document.id == doc.id).first()
    if document:
        document.classification = {"type": classification_type}
        db.commit()

    return {
        "id": doc.id,
        "classification": classification_type
    }


@app.get("/documents/{id}/metadata")
def fetch_document_metadata(id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")


    try:
        file_stat = os.stat(document.file_url)
        file_metadata = {
            "file_size": file_stat.st_size,  
            "created_at": time.ctime(file_stat.st_ctime), 
            "modified_at": time.ctime(file_stat.st_mtime),  
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")

    return {
        "id": document.id,
        "metadata": file_metadata
    }
