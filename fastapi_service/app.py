import os
import time
from fastapi import FastAPI, HTTPException, Depends
from fastapi_jwt_auth import AuthJWT
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from prometheus_fastapi_instrumentator import Instrumentator
from database import SessionLocal, engine
from models import Document
import logging

# Setup logging
logger = logging.getLogger("fastapi-app")
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI app
app = FastAPI()


Instrumentator().instrument(app).expose(app, endpoint="/metrics")


Base = declarative_base()
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# JWT Auth configuration
class Settings(BaseModel):
    authjwt_secret_key: str = os.getenv("SECRET_KEY", "your-secret-key")

@AuthJWT.load_config
def get_config():
    return Settings()


class DocumentRequest(BaseModel):
    id: int
    file_path: str


@app.get("/")
def read_root():
    return {"Hello": "World"}

# Classify document endpoint
@app.post("/classify")
def classify_document(doc: DocumentRequest, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()
    
    try:
        file_path = os.path.join('/app/uploads', doc.file_path)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        classification_type = classify_content(file_path)
        
        document = db.query(Document).filter(Document.id == doc.id).first()
        if document:
            document.classification = {"type": classification_type}
            db.commit()

        return {"id": doc.id, "classification": classification_type}
    except Exception as e:
        logger.error(f"Error classifying document: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Fetch document metadata endpoint
@app.get("/documents/{id}/metadata")
def fetch_document_metadata(id: int, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()
    
    try:
        document = db.query(Document).filter(Document.id == id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        file_path = os.path.join('/app', document.file_url)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        file_stat = os.stat(file_path)
        file_metadata = {
            "file_size": file_stat.st_size,
            "created_at": time.ctime(file_stat.st_ctime),
            "modified_at": time.ctime(file_stat.st_mtime),
        }

        return {"id": document.id, "metadata": file_metadata}
    except Exception as e:
        logger.error(f"Error fetching metadata: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Helper function to classify content based on file extension
def classify_content(file_path: str):
    _, ext = os.path.splitext(file_path)
    if ext == ".txt":
        return "text file"
    elif ext == ".pdf":
        return "PDF document"
    elif ext in [".jpg", ".jpeg", ".png", ".gif"]:
        return "image file"
    else:
        return "binary file"
