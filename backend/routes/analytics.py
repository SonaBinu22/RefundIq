"""Analytics API (Feature 3)"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')


def _require_perm(perm):
    from backend.models import User
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user or not user.has_permission(perm):
        return None, jsonify({'error': 'Insufficient permissions'}), 403
    return user, None, None


@analytics_bp.route('/summary', methods=['GET'])
@jwt_required()
def summary():
    from backend.models import RefundRequest, User
    user, err, code = _require_perm('view_analytics')
    if err:
        return err, code

    total   = RefundRequest.query.count()
    pending = RefundRequest.query.filter(RefundRequest.status.in_(['pending', 'needs_evidence'])).count()
    approved = RefundRequest.query.filter_by(status='approved').count()
    rejected = RefundRequest.query.filter_by(status='rejected').count()
    high_risk = RefundRequest.query.filter_by(risk_level='High Risk').count()
    avg_score = RefundRequest.query.with_entities(func.avg(RefundRequest.risk_score)).scalar() or 0

    return jsonify({
        'total': total,
        'pending': pending,
        'approved': approved,
        'rejected': rejected,
        'high_risk': high_risk,
        'avg_risk_score': round(float(avg_score), 1),
        'fraud_rate': round(high_risk / total * 100, 1) if total else 0
    })


@analytics_bp.route('/monthly', methods=['GET'])
@jwt_required()
def monthly():
    from backend.models import RefundRequest
    user, err, code = _require_perm('view_analytics')
    if err:
        return err, code

    months = []
    for i in range(5, -1, -1):
        start = (datetime.utcnow().replace(day=1) - timedelta(days=i*30)).replace(day=1)
        end   = (start + timedelta(days=32)).replace(day=1)
        count = RefundRequest.query.filter(
            RefundRequest.created_at >= start,
            RefundRequest.created_at < end
        ).count()
        high = RefundRequest.query.filter(
            RefundRequest.created_at >= start,
            RefundRequest.created_at < end,
            RefundRequest.risk_level == 'High Risk'
        ).count()
        months.append({
            'month': start.strftime('%b %Y'),
            'total': count,
            'high_risk': high
        })
    return jsonify({'monthly': months})


@analytics_bp.route('/reasons', methods=['GET'])
@jwt_required()
def reasons():
    from backend.models import RefundRequest
    user, err, code = _require_perm('view_analytics')
    if err:
        return err, code

    rows = (RefundRequest.query
            .with_entities(RefundRequest.refund_reason, func.count(RefundRequest.refund_id))
            .group_by(RefundRequest.refund_reason)
            .order_by(func.count(RefundRequest.refund_id).desc())
            .limit(8).all())
    return jsonify({'reasons': [{'reason': r or 'other', 'count': c} for r, c in rows]})


@analytics_bp.route('/risk-distribution', methods=['GET'])
@jwt_required()
def risk_distribution():
    from backend.models import RefundRequest
    user, err, code = _require_perm('view_analytics')
    if err:
        return err, code

    rows = (RefundRequest.query
            .with_entities(RefundRequest.risk_level, func.count(RefundRequest.refund_id))
            .group_by(RefundRequest.risk_level).all())
    return jsonify({'distribution': [{'level': r, 'count': c} for r, c in rows]})


@analytics_bp.route('/high-risk-users', methods=['GET'])
@jwt_required()
def high_risk_users():
    from backend.models import RefundRequest, User
    user, err, code = _require_perm('view_analytics')
    if err:
        return err, code

    rows = (RefundRequest.query
            .with_entities(RefundRequest.user_id, func.count(RefundRequest.refund_id),
                           func.avg(RefundRequest.risk_score))
            .filter(RefundRequest.risk_level == 'High Risk')
            .group_by(RefundRequest.user_id)
            .order_by(func.count(RefundRequest.refund_id).desc())
            .limit(10).all())

    result = []
    for uid, count, avg in rows:
        u = User.query.get(uid)
        result.append({
            'user_id': uid,
            'name': u.name if u else '—',
            'email': u.email if u else '—',
            'high_risk_count': count,
            'avg_score': round(float(avg), 1)
        })
    return jsonify({'users': result})
