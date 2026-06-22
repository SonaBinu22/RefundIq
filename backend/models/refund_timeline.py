from datetime import datetime
from .db import db


class RefundTimeline(db.Model):
    __tablename__ = 'refund_timeline'

    id = db.Column(db.Integer, primary_key=True)
    refund_id = db.Column(db.Integer, db.ForeignKey('refund_requests.refund_id'), nullable=False)
    event = db.Column(db.String(100), nullable=False)
    detail = db.Column(db.Text)
    actor = db.Column(db.String(100))   # 'system' | 'admin:<id>' | 'user:<id>'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'refund_id': self.refund_id,
            'event': self.event,
            'detail': self.detail,
            'actor': self.actor,
            'created_at': self.created_at.isoformat()
        }
