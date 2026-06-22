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
    from backend.models import db, User, RefundRequest, Evidence, FraudExplanation, SimilarityResult
    from backend.fraud_detection import analyze_image, analyze_video, validate_invoice, calculate_risk_score
    from backend.services.explanation_service import build_explanation
    from backend.services.similarity_service import compare_descriptions, get_embedding
    from backend.services.timeline_service import log_event
    from backend.services.audit_service import log as audit_log
    from backend.services import email_service

    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    if not user.has_permission('submit_refund'):
        return jsonify({'error': 'Permission denied'}), 403

    product_name  = request.form.get('product_name', '').strip()
    order_id      = request.form.get('order_id', '').strip()
    purchase_date = request.form.get('purchase_date', '')
    refund_amount = request.form.get('refund_amount', 0)
    refund_reason = request.form.get('refund_reason', '').strip()
    description   = request.form.get('description', '').strip()

    if not product_name or not order_id or not refund_amount:
        return jsonify({'error': 'product_name, order_id, and refund_amount are required'}), 400

    try:
        refund_amount = float(refund_amount)
    except ValueError:
        return jsonify({'error': 'Invalid refund_amount'}), 400

    thirty_ago    = datetime.utcnow() - timedelta(days=30)
    recent_count  = RefundRequest.query.filter(RefundRequest.user_id == uid,
                                               RefundRequest.created_at >= thirty_ago).count()
    total_count   = RefundRequest.query.filter_by(user_id=uid).count()

    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)

    image_result = video_result = invoice_result = None
    has_image = has_video = has_invoice = False
    saved_files = []

    for _, file in request.files.items():
        if not file or not file.filename or not allowed_file(file.filename):
            continue
        fname = secure_filename(file.filename)
        fpath = os.path.join(upload_folder, fname)
        file.save(fpath)
        ftype = get_file_type(fname)
        if ftype == 'image':
            has_image = True
            image_result = analyze_image(fpath)
            saved_files.append((fpath, ftype, file.filename, json.dumps(image_result)))
        elif ftype == 'video':
            has_video = True
            video_result = analyze_video(fpath)
            saved_files.append((fpath, ftype, file.filename, json.dumps(video_result)))
        elif ftype == 'invoice':
            has_invoice = True
            invoice_result = validate_invoice(fpath, claimed_order_id=order_id,
                                              claimed_amount=refund_amount, claimed_product=product_name)
            saved_files.append((fpath, ftype, file.filename, json.dumps(invoice_result)))

    # Risk scoring
    risk = calculate_risk_score(
        image_result=image_result, video_result=video_result,
        invoice_result=invoice_result, has_image=has_image,
        has_video=has_video, has_invoice=has_invoice,
        user_refund_count=total_count, recent_refund_count=recent_count
    )

    # Semantic similarity check
    full_text = f"{product_name} {refund_reason} {description}".strip()
    existing = []
    for prev in RefundRequest.query.filter(RefundRequest.user_id != uid).limit(200).all():
        prev_text = f"{prev.product_name} {prev.refund_reason or ''} {prev.description or ''}".strip()
        existing.append({'refund_id': prev.refund_id, 'description': prev_text, 'embedding': []})

    sim_result = compare_descriptions(full_text, existing)
    if sim_result.get('flagged'):
        risk['risk_score'] = min(risk['risk_score'] + 20, 100)
        risk['breakdown'].append({'factor': 'Semantically similar to previous refund', 'points': 20})
        risk['recommendations'].append('Investigate possible duplicate claim')

    status = 'needs_evidence' if risk['risk_score'] >= 61 else 'pending'

    # Persist refund
    refund = RefundRequest(
        user_id=uid, product_name=product_name, order_id=order_id,
        purchase_date=purchase_date, refund_amount=refund_amount,
        refund_reason=refund_reason, description=description,
        status=status, risk_score=risk['risk_score'], risk_level=risk['risk_level']
    )
    db.session.add(refund)
    db.session.flush()

    for fpath, ftype, orig, analysis_json in saved_files:
        db.session.add(Evidence(refund_id=refund.refund_id, file_path=fpath,
                                file_type=ftype, original_filename=orig,
                                analysis_result=analysis_json))

    # Explanation
    explanation = build_explanation(risk, image_result, video_result, invoice_result)
    exp_row = FraudExplanation(
        refund_id=refund.refund_id,
        risk_score=risk['risk_score'],
        risk_level=risk['risk_level'],
        narrative=explanation['narrative'],
        factors=json.dumps(explanation['factors']),
        recommendations=json.dumps(explanation['recommendations'])
    )
    db.session.add(exp_row)

    # Similarity record
    if sim_result.get('similarity_score', 0) > 0:
        db.session.add(SimilarityResult(
            refund_id=refund.refund_id,
            matched_refund_id=sim_result.get('matched_refund_id'),
            similarity_score=sim_result['similarity_score'],
            fraud_probability=sim_result['fraud_probability'],
            flagged=sim_result['flagged']
        ))

    # Timeline
    log_event(refund.refund_id, 'created', f'Submitted by {user.name}', actor=f'user:{uid}')
    if saved_files:
        log_event(refund.refund_id, 'evidence_uploaded',
                  f'{len(saved_files)} file(s) uploaded', actor=f'user:{uid}')
    log_event(refund.refund_id, 'fraud_analysis_done',
              f'Risk score: {risk["risk_score"]}/100 ({risk["risk_level"]})', actor='system')
    if sim_result.get('flagged'):
        log_event(refund.refund_id, 'similarity_checked',
                  f'Similarity {sim_result["similarity_score"]} to refund #{sim_result.get("matched_refund_id")}',
                  actor='system')

    # Audit
    audit_log('submit_refund', 'RefundRequest', refund.refund_id,
              new_value=f'status={status},score={risk["risk_score"]}', user_id=uid)

    db.session.commit()

    # Email
    try:
        email_service.send_refund_submitted(user.email, user.name, refund.refund_id,
                                             product_name, risk['risk_level'])
    except Exception:
        pass

    return jsonify({
        'message': 'Refund request submitted',
        'refund_id': refund.refund_id,
        'status': status,
        'risk_score': risk['risk_score'],
        'risk_level': risk['risk_level'],
        'narrative': explanation['narrative'],
        'factors': explanation['factors'],
        'recommendations': explanation['recommendations'],
        'similarity': sim_result if sim_result.get('similarity_score', 0) > 0 else None
    }), 201


@refund_bp.route('/my-refunds', methods=['GET'])
@jwt_required()
def get_my_refunds():
    from backend.models import RefundRequest
    uid = int(get_jwt_identity())
    refunds = RefundRequest.query.filter_by(user_id=uid)\
        .order_by(RefundRequest.created_at.desc()).all()
    return jsonify({'refunds': [r.to_dict() for r in refunds]})


@refund_bp.route('/refund/<int:refund_id>', methods=['GET'])
@jwt_required()
def get_refund(refund_id):
    from backend.models import User, RefundRequest, FraudExplanation, SimilarityResult
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

    return jsonify({
        'refund': refund.to_dict(),
        'explanation': exp.to_dict() if exp else None,
        'similarity': sim.to_dict() if sim else None,
        'timeline': get_timeline(refund_id)
    })
