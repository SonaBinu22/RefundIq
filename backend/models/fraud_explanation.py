from datetime import datetime
from .db import db


class FraudExplanation(db.Model):
    __tablename__ = 'fraud_explanations'

    id = db.Column(db.Integer, primary_key=True)
    refund_id = db.Column(db.Integer, db.ForeignKey('refund_requests.refund_id'), nullable=False, unique=True)
    risk_score = db.Column(db.Integer, default=0)
    risk_level = db.Column(db.String(20))
    narrative = db.Column(db.Text)           # AI-generated human-readable summary
    factors = db.Column(db.Text)             # JSON list of {factor, impact, detail}
    recommendations = db.Column(db.Text)     # JSON list of strings
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'refund_id': self.refund_id,
            'risk_score': self.risk_score,
            'risk_level': self.risk_level,
            'narrative': self.narrative,
            'factors': json.loads(self.factors) if self.factors else [],
            'recommendations': json.loads(self.recommendations) if self.recommendations else [],
            'created_at': self.created_at.isoformat()
        }
