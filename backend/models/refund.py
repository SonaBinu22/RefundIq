from datetime import datetime
from .db import db

class RefundRequest(db.Model):
    __tablename__ = 'refund_requests'

    refund_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    order_id = db.Column(db.String(100), nullable=False)
    purchase_date = db.Column(db.String(20))
    refund_amount = db.Column(db.Float, nullable=False)
    refund_reason = db.Column(db.String(100))
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending | approved | rejected | needs_evidence
    risk_score = db.Column(db.Integer, default=0)
    risk_level = db.Column(db.String(20), default='Low Risk')
    admin_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    evidence = db.relationship('Evidence', backref='refund', lazy=True)
    admin_logs = db.relationship('AdminLog', backref='refund', lazy=True)

    def to_dict(self):
        return {
            'refund_id': self.refund_id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'user_email': self.user.email if self.user else None,
            'product_name': self.product_name,
            'order_id': self.order_id,
            'purchase_date': self.purchase_date,
            'refund_amount': self.refund_amount,
            'refund_reason': self.refund_reason,
            'description': self.description,
            'status': self.status,
            'risk_score': self.risk_score,
            'risk_level': self.risk_level,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat(),
            'evidence': [e.to_dict() for e in self.evidence]
        }
