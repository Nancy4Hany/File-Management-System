from config.extensions import db

class Log(db.Model):
    __tablename__ = 'logs'

    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(10), nullable=False)  
    message = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime(), default=db.func.now(), nullable=False)

    @property
    def data(self):
        return {
            'id': self.id,
            'level': self.level,
            'message': self.message,
            'timestamp': self.timestamp,
        }
