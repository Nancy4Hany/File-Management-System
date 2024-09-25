
from extensions import db
from datetime import datetime

class Document(db.Model):
    __tablename__ = 'documents' 

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    file_url = db.Column(db.String(200), nullable=False)
    

    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    

    uploader = db.relationship('User', backref='documents')
    
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_processed = db.Column(db.Boolean, default=False)
    processed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), default="Pending")
    

    document_metadata = db.Column(db.JSON)  
    
    classification = db.Column(db.JSON)
