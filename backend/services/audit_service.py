"""
Enterprise Audit Trail Service (Feature 11)
Logs every significant action with user, IP, resource, before/after values.
"""
from flask import request as flask_request
from backend.models.db import db
from backend.models.audit_trail import AuditTrail


def log(action: str, resource: str = None, resource_id=None,
        old_value=None, new_value=None, user_id=None):
    try:
        ip = flask_request.remote_addr if flask_request else None
        ua = flask_request.headers.get('User-Agent', '')[:300] if flask_request else None
    except RuntimeError:
        ip, ua = None, None

    entry = AuditTrail(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=str(resource_id) if resource_id else None,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
        ip_address=ip,
        user_agent=ua
    )
    db.session.add(entry)
    db.session.flush()


def get_audit_log(page=1, per_page=50, user_id=None, action=None, resource=None):
    q = AuditTrail.query
    if user_id:
        q = q.filter_by(user_id=user_id)
    if action:
        q = q.filter(AuditTrail.action.ilike(f'%{action}%'))
    if resource:
        q = q.filter(AuditTrail.resource.ilike(f'%{resource}%'))
    q = q.order_by(AuditTrail.created_at.desc())
    paginated = q.paginate(page=page, per_page=per_page, error_out=False)
    return {
        'items': [i.to_dict() for i in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'page': page
    }
