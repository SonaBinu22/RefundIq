from datetime import datetime
from .db import db


class SimilarityResult(db.Model):
    __tablename__ = 'similarity_results'

    id = db.Column(db.Integer, primary_key=True)
    refund_id = db.Column(db.Integer, db.ForeignKey('refund_requests.refund_id'), nullable=False)
    matched_refund_id = db.Column(db.Integer, db.ForeignKey('refund_requests.refund_id'), nullable=True)
    similarity_score = db.Column(db.Float, default=0.0)
    fraud_probability = db.Column(db.Float, default=0.0)
    flagged = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'refund_id': self.refund_id,
            'matched_refund_id': self.matched_refund_id,
            'similarity_score': round(self.similarity_score, 4),
            'fraud_probability': round(self.fraud_probability, 4),
            'flagged': self.flagged,
            'created_at': self.created_at.isoformat()
        }
