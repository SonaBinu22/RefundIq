from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


def _require_perm(perm):
    from backend.models import User
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user or not user.has_permission(perm):
        return None, jsonify({'error': 'Insufficient permissions'}), 403
    return user, None, None


@admin_bp.route('/refunds', methods=['GET'])
@jwt_required()
def list_all_refunds():
    from backend.models import RefundRequest
    user, err, code = _require_perm('view_all_refunds')
    if err:
        return err, code

    status_filter = request.args.get('status')
    risk_filter   = request.args.get('risk_level')
    page          = request.args.get('page', 1, type=int)

    q = RefundRequest.query
    if status_filter:
        q = q.filter_by(status=status_filter)
    if risk_filter:
        q = q.filter_by(risk_level=risk_filter)

    paginated = q.order_by(RefundRequest.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return jsonify({
        'refunds': [r.to_dict() for r in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'page': page
    })


@admin_bp.route('/refund/<int:refund_id>', methods=['GET'])
@jwt_required()
def get_refund_detail(refund_id):
    from backend.models import RefundRequest, FraudExplanation, SimilarityResult
    from backend.services.timeline_service import get_timeline
    user, err, code = _require_perm('view_all_refunds')
    if err:
        return err, code

    refund = RefundRequest.query.get(refund_id)
    if not refund:
        return jsonify({'error': 'Not found'}), 404

    exp = FraudExplanation.query.filter_by(refund_id=refund_id).first()
    sim = SimilarityResult.query.filter_by(refund_id=refund_id).first()

    return jsonify({
        'refund': refund.to_dict(),
        'explanation': exp.to_dict() if exp else None,
        'similarity': sim.to_dict() if sim else None,
        'timeline': get_timeline(refund_id)
    })


@admin_bp.route('/refund/<int:refund_id>/decision', methods=['POST'])
@jwt_required()
def make_decision(refund_id):
    from backend.models import db, User, RefundRequest, AdminLog
    from backend.services.timeline_service import log_event
    from backend.services.audit_service import log as audit_log
    from backend.services import email_service

    admin, err, code = _require_perm('approve_refunds')
    if err:
        return err, code

    refund = RefundRequest.query.get(refund_id)
    if not refund:
        return jsonify({'error': 'Not found'}), 404

    data       = request.get_json() or {}
    new_status = data.get('status')
    notes      = data.get('notes', '')

    valid = {'approved', 'rejected', 'pending', 'needs_evidence'}
    if new_status not in valid:
        return jsonify({'error': f'status must be one of {valid}'}), 400

    old_status    = refund.status
    refund.status = new_status
    if notes:
        refund.admin_notes = notes

    db.session.add(AdminLog(admin_id=admin.user_id, refund_id=refund_id,
                             action=new_status, notes=notes))
    log_event(refund_id, new_status, notes or None, actor=f'admin:{admin.user_id}')
    audit_log('refund_decision', 'RefundRequest', refund_id,
              old_value=old_status, new_value=new_status, user_id=admin.user_id)
    db.session.commit()

    # Email customer
    customer = refund.user
    if customer:
        try:
            if new_status == 'approved':
                email_service.send_refund_approved(customer.email, customer.name, refund_id, refund.product_name)
            elif new_status == 'rejected':
                email_service.send_refund_rejected(customer.email, customer.name, refund_id, refund.product_name, notes)
            elif new_status == 'needs_evidence':
                email_service.send_evidence_requested(customer.email, customer.name, refund_id, notes)
        except Exception:
            pass

    return jsonify({'message': f'Refund {new_status}', 'refund': refund.to_dict()})


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    from backend.models import User
    user, err, code = _require_perm('view_all_refunds')
    if err:
        return err, code
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({'users': [u.to_dict() for u in users]})


@admin_bp.route('/user/<int:target_id>/role', methods=['POST'])
@jwt_required()
def change_role(target_id):
    from backend.models import db, User
    from backend.services.audit_service import log as audit_log
    admin, err, code = _require_perm('*')
    if err:
        # check superadmin explicitly
        uid = int(get_jwt_identity())
        u = User.query.get(uid)
        if not u or u.role != 'superadmin':
            return jsonify({'error': 'Superadmin required'}), 403
        admin = u

    target = User.query.get(target_id)
    if not target:
        return jsonify({'error': 'User not found'}), 404

    data     = request.get_json() or {}
    new_role = data.get('role')
    from backend.models.user import ROLES
    if new_role not in ROLES:
        return jsonify({'error': f'role must be one of {ROLES}'}), 400

    old_role      = target.role
    target.role   = new_role
    audit_log('role_change', 'User', target_id, old_value=old_role, new_value=new_role, user_id=admin.user_id)
    db.session.commit()
    return jsonify({'message': f'Role updated to {new_role}', 'user': target.to_dict()})
