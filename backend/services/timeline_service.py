"""
Refund Timeline Service (Feature 4)
Records every state change and action on a refund.
"""
from backend.models.db import db
from backend.models.refund_timeline import RefundTimeline


EVENTS = {
    'created':              'Refund Created',
    'evidence_uploaded':    'Evidence Uploaded',
    'invoice_verified':     'Invoice Verified',
    'fraud_analysis_done':  'Fraud Analysis Completed',
    'similarity_checked':   'Duplicate Check Completed',
    'admin_review_started': 'Admin Review Started',
    'approved':             'Refund Approved',
    'rejected':             'Refund Rejected',
    'needs_evidence':       'Additional Evidence Requested',
    'password_changed':     'Password Changed',
    'status_changed':       'Status Updated',
}


def log_event(refund_id: int, event_key: str, detail: str = None, actor: str = 'system'):
    event_label = EVENTS.get(event_key, event_key)
    entry = RefundTimeline(
        refund_id=refund_id,
        event=event_label,
        detail=detail,
        actor=actor
    )
    db.session.add(entry)
    # Flush so caller can commit in bulk
    db.session.flush()


def get_timeline(refund_id: int) -> list:
    entries = RefundTimeline.query.filter_by(refund_id=refund_id)\
        .order_by(RefundTimeline.created_at.asc()).all()
    return [e.to_dict() for e in entries]
