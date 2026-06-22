from datetime import datetime
from .db import db


class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    refund_id = db.Column(db.Integer, db.ForeignKey('refund_requests.refund_id'), nullable=True)
    role = db.Column(db.String(10), nullable=False)   # 'user' | 'assistant'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'refund_id': self.refund_id,
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }
