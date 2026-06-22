from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


def _get_admin():
    from backend.models import User
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return None, jsonify({'error': 'Admin access required'}), 403
    return user, None, None


@admin_bp.route('/refunds', methods=['GET'])
@jwt_required()
def list_all_refunds():
    from backend.models import RefundRequest
    admin, err, code = _get_admin()
    if err:
        return err, code

    status_filter = request.args.get('status')
    risk_filter = request.args.get('risk_level')
    query = RefundRequest.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    if risk_filter:
        query = query.filter_by(risk_level=risk_filter)

    refunds = query.order_by(RefundRequest.created_at.desc()).all()
    return jsonify({'refunds': [r.to_dict() for r in refunds]}), 200


@admin_bp.route('/refund/<int:refund_id>/decision', methods=['POST'])
@jwt_required()
def make_decision(refund_id):
    from backend.models import db, RefundRequest, AdminLog
    admin, err, code = _get_admin()
    if err:
        return err, code

    refund = RefundRequest.query.get(refund_id)
    if not refund:
        return jsonify({'error': 'Refund not found'}), 404

    data = request.get_json() or {}
    new_status = data.get('status')
    notes = data.get('notes', '')

    valid_statuses = {'approved', 'rejected', 'pending', 'needs_evidence'}
    if new_status not in valid_statuses:
        return jsonify({'error': f'status must be one of {valid_statuses}'}), 400

    refund.status = new_status
    if notes:
        refund.admin_notes = notes

    db.session.add(AdminLog(
        admin_id=admin.user_id,
        refund_id=refund_id,
        action=new_status,
        notes=notes
    ))
    db.session.commit()

    return jsonify({'message': f'Refund {new_status}', 'refund': refund.to_dict()}), 200


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    from backend.models import User
    admin, err, code = _get_admin()
    if err:
        return err, code
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({'users': [u.to_dict() for u in users]}), 200
