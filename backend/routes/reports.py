"""PDF Report + Audit Trail routes (Features 11, 14)"""
from flask import Blueprint, jsonify, request, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity

reports_bp = Blueprint('reports', __name__, url_prefix='/api')


@reports_bp.route('/refund/<int:refund_id>/report', methods=['GET'])
@jwt_required()
def download_report(refund_id):
    from backend.models import User, RefundRequest, FraudExplanation, SimilarityResult
    from backend.services.pdf_service import generate_refund_report
    from backend.services.timeline_service import get_timeline

    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    refund = RefundRequest.query.get(refund_id)

    if not refund:
        return jsonify({'error': 'Not found'}), 404
    if not user.has_permission('view_all_refunds') and refund.user_id != uid:
        return jsonify({'error': 'Unauthorized'}), 403

    exp = FraudExplanation.query.filter_by(refund_id=refund_id).first()
    sim = SimilarityResult.query.filter_by(refund_id=refund_id).first()
    timeline = get_timeline(refund_id)

    pdf = generate_refund_report(
        refund=refund.to_dict(),
        explanation=exp.to_dict() if exp else None,
        timeline=timeline,
        similarity=sim.to_dict() if sim else None
    )

    resp = make_response(pdf)
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = f'attachment; filename=refund_{refund_id}_report.pdf'
    return resp


@reports_bp.route('/admin/audit', methods=['GET'])
@jwt_required()
def get_audit():
    from backend.models import User
    from backend.services.audit_service import get_audit_log
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user or not user.has_permission('view_audit'):
        return jsonify({'error': 'Insufficient permissions'}), 403

    page     = request.args.get('page', 1, type=int)
    action   = request.args.get('action')
    resource = request.args.get('resource')
    filter_uid = request.args.get('user_id', type=int)

    return jsonify(get_audit_log(page=page, per_page=50,
                                  user_id=filter_uid, action=action, resource=resource))


@reports_bp.route('/refund/<int:refund_id>/timeline', methods=['GET'])
@jwt_required()
def get_timeline_route(refund_id):
    from backend.models import User, RefundRequest
    from backend.services.timeline_service import get_timeline
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    refund = RefundRequest.query.get(refund_id)
    if not refund:
        return jsonify({'error': 'Not found'}), 404
    if not user.has_permission('view_all_refunds') and refund.user_id != uid:
        return jsonify({'error': 'Unauthorized'}), 403
    return jsonify({'timeline': get_timeline(refund_id)})
