import os
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

refund_bp = Blueprint('refund', __name__, url_prefix='/api')

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'mp4', 'pdf'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_type(filename):
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext in {'jpg', 'jpeg', 'png'}:
        return 'image'
    if ext == 'mp4':
        return 'video'
    if ext == 'pdf':
        return 'invoice'
    return 'other'


@refund_bp.route('/submit-refund', methods=['POST'])
@jwt_required()
def submit_refund():
    from backend.models import db, User, RefundRequest, Evidence
    from backend.fraud_detection import analyze_image, analyze_video, validate_invoice, calculate_risk_score

    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    product_name = request.form.get('product_name', '').strip()
    order_id = request.form.get('order_id', '').strip()
    purchase_date = request.form.get('purchase_date', '')
    refund_amount = request.form.get('refund_amount', 0)
    refund_reason = request.form.get('refund_reason', '').strip()
    description = request.form.get('description', '').strip()

    if not product_name or not order_id or not refund_amount:
        return jsonify({'error': 'product_name, order_id, and refund_amount are required'}), 400

    try:
        refund_amount = float(refund_amount)
    except ValueError:
        return jsonify({'error': 'Invalid refund_amount'}), 400

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_count = RefundRequest.query.filter(
        RefundRequest.user_id == user_id,
        RefundRequest.created_at >= thirty_days_ago
    ).count()
    total_count = RefundRequest.query.filter_by(user_id=user_id).count()

    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)

    image_result = None
    video_result = None
    invoice_result = None
    has_image = False
    has_video = False
    has_invoice = False
    saved_files = []

    for field_name, file in request.files.items():
        if not file or not file.filename:
            continue
        if not allowed_file(file.filename):
            continue
        fname = secure_filename(file.filename)
        file_path = os.path.join(upload_folder, fname)
        file.save(file_path)
        ftype = get_file_type(fname)

        if ftype == 'image':
            has_image = True
            image_result = analyze_image(file_path)
            saved_files.append((file_path, ftype, file.filename, json.dumps(image_result)))
        elif ftype == 'video':
            has_video = True
            video_result = analyze_video(file_path)
            saved_files.append((file_path, ftype, file.filename, json.dumps(video_result)))
        elif ftype == 'invoice':
            has_invoice = True
            invoice_result = validate_invoice(
                file_path,
                claimed_order_id=order_id,
                claimed_amount=refund_amount,
                claimed_product=product_name
            )
            saved_files.append((file_path, ftype, file.filename, json.dumps(invoice_result)))

    risk = calculate_risk_score(
        image_result=image_result,
        video_result=video_result,
        invoice_result=invoice_result,
        has_image=has_image,
        has_video=has_video,
        has_invoice=has_invoice,
        user_refund_count=total_count,
        recent_refund_count=recent_count
    )

    status = 'needs_evidence' if risk['risk_score'] >= 61 else 'pending'

    refund = RefundRequest(
        user_id=user_id,
        product_name=product_name,
        order_id=order_id,
        purchase_date=purchase_date,
        refund_amount=refund_amount,
        refund_reason=refund_reason,
        description=description,
        status=status,
        risk_score=risk['risk_score'],
        risk_level=risk['risk_level']
    )
    db.session.add(refund)
    db.session.flush()

    for file_path, ftype, original_name, analysis_json in saved_files:
        db.session.add(Evidence(
            refund_id=refund.refund_id,
            file_path=file_path,
            file_type=ftype,
            original_filename=original_name,
            analysis_result=analysis_json
        ))

    db.session.commit()

    return jsonify({
        'message': 'Refund request submitted successfully',
        'refund_id': refund.refund_id,
        'status': status,
        'risk_score': risk['risk_score'],
        'risk_level': risk['risk_level'],
        'breakdown': risk['breakdown'],
        'recommendations': risk['recommendations']
    }), 201


@refund_bp.route('/my-refunds', methods=['GET'])
@jwt_required()
def get_my_refunds():
    from backend.models import RefundRequest
    user_id = int(get_jwt_identity())
    refunds = RefundRequest.query.filter_by(user_id=user_id)\
        .order_by(RefundRequest.created_at.desc()).all()
    return jsonify({'refunds': [r.to_dict() for r in refunds]}), 200


@refund_bp.route('/refund/<int:refund_id>', methods=['GET'])
@jwt_required()
def get_refund(refund_id):
    from backend.models import User, RefundRequest
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    refund = RefundRequest.query.get(refund_id)
    if not refund:
        return jsonify({'error': 'Refund not found'}), 404
    if user.role != 'admin' and refund.user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    return jsonify({'refund': refund.to_dict()}), 200
