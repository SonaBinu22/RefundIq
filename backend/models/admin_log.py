from datetime import datetime
from .db import db

class AdminLog(db.Model):
    __tablename__ = 'admin_logs'

    log_id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    refund_id = db.Column(db.Integer, db.ForeignKey('refund_requests.refund_id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'log_id': self.log_id,
            'admin_id': self.admin_id,
            'refund_id': self.refund_id,
            'action': self.action,
            'notes': self.notes,
            'timestamp': self.timestamp.isoformat()
        }
