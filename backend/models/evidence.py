from datetime import datetime
from .db import db

class Evidence(db.Model):
    __tablename__ = 'evidence'

    evidence_id = db.Column(db.Integer, primary_key=True)
    refund_id = db.Column(db.Integer, db.ForeignKey('refund_requests.refund_id'), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(20))  # image | video | invoice
    original_filename = db.Column(db.String(255))
    analysis_result = db.Column(db.Text)  # JSON string
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        import json
        result = None
        try:
            result = json.loads(self.analysis_result) if self.analysis_result else None
        except Exception:
            result = self.analysis_result
        return {
            'evidence_id': self.evidence_id,
            'refund_id': self.refund_id,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'original_filename': self.original_filename,
            'analysis_result': result,
            'uploaded_at': self.uploaded_at.isoformat()
        }
