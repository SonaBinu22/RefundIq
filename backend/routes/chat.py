"""AI Chat Assistant API (Feature 6)"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')


@chat_bp.route('/message', methods=['POST'])
@jwt_required()
def send_message():
    from backend.models import db, User, RefundRequest, ChatMessage, FraudExplanation
    from backend.services.chat_service import get_response
    from backend.models.fraud_explanation import FraudExplanation

    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json() or {}
    message = data.get('message', '').strip()
    refund_id = data.get('refund_id')

    if not message:
        return jsonify({'error': 'message is required'}), 400

    # Build context
    context = {}
    if refund_id:
        refund = RefundRequest.query.get(refund_id)
        if refund and (refund.user_id == uid or user.has_permission('view_all_refunds')):
            context = {
                'refund_id': refund.refund_id,
                'status': refund.status,
                'risk_score': refund.risk_score,
                'risk_level': refund.risk_level,
                'product': refund.product_name,
            }
            exp = FraudExplanation.query.filter_by(refund_id=refund_id).first()
            if exp:
                context['factors'] = exp.to_dict().get('factors', [])

    # Get history (last 10 messages)
    history_rows = (ChatMessage.query
                    .filter_by(user_id=uid)
                    .order_by(ChatMessage.created_at.desc())
                    .limit(10).all())
    history = [{'role': m.role, 'content': m.content} for m in reversed(history_rows)]

    # Get AI response
    response = get_response(message, context, history)

    # Store both sides
    db.session.add(ChatMessage(user_id=uid, refund_id=refund_id, role='user', content=message))
    db.session.add(ChatMessage(user_id=uid, refund_id=refund_id, role='assistant', content=response))
    db.session.commit()

    return jsonify({'response': response, 'refund_id': refund_id})


@chat_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    from backend.models import ChatMessage
    uid = int(get_jwt_identity())
    refund_id = request.args.get('refund_id', type=int)
    q = ChatMessage.query.filter_by(user_id=uid)
    if refund_id:
        q = q.filter_by(refund_id=refund_id)
    msgs = q.order_by(ChatMessage.created_at.asc()).limit(50).all()
    return jsonify({'messages': [m.to_dict() for m in msgs]})
