"""
Explainable AI Fraud Report Service (Feature 1 + 7)
Converts raw risk engine output into human-readable explanations and narratives.
"""
import json


FACTOR_LABELS = {
    'No image evidence provided':           ('missing_evidence',   'high',   'No photo or video was submitted to support the claim.'),
    'blurry':                               ('image_quality',      'medium', 'The uploaded image is blurry and cannot be properly verified.'),
    'duplicate':                            ('duplicate_evidence', 'high',   'The uploaded image matches a previously submitted claim.'),
    'manipulation':                         ('image_tampered',     'high',   'Signs of digital manipulation were detected in the image.'),
    'Invoice data mismatch':                ('invoice_mismatch',   'high',   'Invoice details do not match the submitted order information.'),
    'OCR not available':                    ('ocr_unavailable',    'low',    'Invoice OCR is unavailable; manual verification required.'),
    'Video quality is low':                 ('video_quality',      'medium', 'Video evidence is low quality and difficult to verify.'),
    'video appears to be a repeated':       ('video_slideshow',    'high',   'Video appears to be a slideshow of static images, not genuine footage.'),
    'refund requests in last 30 days':      ('repeat_behavior',    'high',   'Customer has submitted multiple refund requests recently.'),
    'recent refund requests':               ('repeat_behavior',    'medium', 'Customer has a pattern of recent refund activity.'),
}

IMPACT_POINTS = {'high': 'High Impact', 'medium': 'Medium Impact', 'low': 'Low Impact'}


def build_explanation(risk_result: dict, image_result=None, video_result=None, invoice_result=None) -> dict:
    """
    Build structured explanation from risk engine output.
    Returns dict with factors list and narrative.
    """
    factors = []
    score = risk_result.get('risk_score', 0)
    level = risk_result.get('risk_level', 'Low Risk')

    for item in risk_result.get('breakdown', []):
        factor_text = item.get('factor', '')
        points = item.get('points', 0)

        label = None
        impact = 'medium'
        detail = factor_text

        for key, (lbl, imp, det) in FACTOR_LABELS.items():
            if key.lower() in factor_text.lower():
                label = lbl
                impact = imp
                detail = det
                break

        factors.append({
            'label': label or 'risk_factor',
            'description': factor_text,
            'detail': detail,
            'impact': IMPACT_POINTS.get(impact, 'Medium Impact'),
            'points': points
        })

    # Add image-specific factors
    if image_result:
        for d in image_result.get('details', []):
            if 'passed' not in d.lower():
                factors.append({
                    'label': 'image_analysis',
                    'description': d,
                    'detail': d,
                    'impact': 'Medium Impact',
                    'points': 0
                })

    narrative = _generate_narrative(score, level, factors)

    return {
        'risk_score': score,
        'risk_level': level,
        'factors': factors,
        'recommendations': risk_result.get('recommendations', []),
        'narrative': narrative
    }


def _generate_narrative(score: int, level: str, factors: list) -> str:
    """Generate a human-readable fraud report narrative."""
    if not factors:
        return (
            f"This refund request received a risk score of {score}/100, "
            f"classified as {level}. No specific fraud indicators were detected. "
            "The request appears consistent with a genuine claim and may proceed through standard processing."
        )

    high = [f for f in factors if f['impact'] == 'High Impact']
    medium = [f for f in factors if f['impact'] == 'Medium Impact']

    parts = [f"This refund request was classified as {level} with a fraud risk score of {score}/100."]

    if high:
        descs = '; '.join(f['description'].lower() for f in high[:3])
        parts.append(f"The primary concerns are: {descs}.")

    if medium:
        descs = '; '.join(f['description'].lower() for f in medium[:2])
        parts.append(f"Additional risk signals include: {descs}.")

    if score >= 70:
        parts.append("Manual review by an administrator is strongly recommended before proceeding.")
    elif score >= 40:
        parts.append("This claim requires careful review before approval.")
    else:
        parts.append("This claim appears low risk but standard verification is advised.")

    return ' '.join(parts)
