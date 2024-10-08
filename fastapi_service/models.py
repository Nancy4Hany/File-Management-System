from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from pydantic import BaseModel
from typing import Dict

class DocumentMetadata(BaseModel):
    file_size: int
    created_at: str
    modified_at: str

class Classification(BaseModel):
    type: str

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(200), nullable=False, unique=True)
    password = Column(String(200), nullable=False)


class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    description = Column(String(500), nullable=True)
    file_url = Column(String(200), nullable=False)
    
    uploaded_by = Column(Integer, ForeignKey('users.id'), nullable=False)  
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    is_processed = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="Pending")

    # Metadata and classification fields
    document_metadata = Column(JSON, nullable=True)  
    classification = Column(JSON, nullable=True) 

    user = relationship("User", back_populates="documents")

User.documents = relationship("Document", back_populates="user")
