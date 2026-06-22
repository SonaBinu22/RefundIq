"""
Fraud Risk Scoring Engine
Aggregates signals from image, video, and invoice analysis
plus behavioral patterns to produce a final risk score.
"""

RISK_WEIGHTS = {
    "missing_evidence": 25,
    "blurred_image": 15,
    "duplicate_upload": 30,
    "invoice_mismatch": 25,
    "suspicious_user_activity": 20,
    "repeated_refund_requests": 20,
    "video_issues": 15,
    "manipulation_detected": 20,
}

RISK_LEVELS = [
    (30, "Low Risk"),
    (60, "Medium Risk"),
    (100, "High Risk"),
]


def _get_risk_level(score):
    for threshold, label in RISK_LEVELS:
        if score <= threshold:
            return label
    return "High Risk"


def calculate_risk_score(
    image_result=None,
    video_result=None,
    invoice_result=None,
    has_image=True,
    has_video=False,
    has_invoice=False,
    user_refund_count=0,
    recent_refund_count=0
):
    """
    Calculate overall fraud risk score.

    Args:
        image_result: dict from image_checker.analyze_image()
        video_result: dict from video_checker.analyze_video()
        invoice_result: dict from ocr_validator.validate_invoice()
        has_image: whether image evidence was submitted
        has_video: whether video evidence was submitted
        has_invoice: whether invoice was submitted
        user_refund_count: total refunds by this user
        recent_refund_count: refunds in last 30 days

    Returns:
        dict: { risk_score, risk_level, breakdown, recommendations }
    """
    total_score = 0
    breakdown = []
    recommendations = []

    # Missing evidence
    if not has_image:
        pts = RISK_WEIGHTS["missing_evidence"]
        total_score += pts
        breakdown.append({"factor": "No image evidence provided", "points": pts})
        recommendations.append("Request customer to upload product damage photos")

    # Image analysis
    if image_result:
        img_pts = image_result.get("risk_points", 0)
        if img_pts > 0:
            total_score += img_pts
            for detail in image_result.get("details", []):
                if "blur" in detail.lower() or "duplic" in detail.lower() or "manipul" in detail.lower():
                    breakdown.append({"factor": detail, "points": img_pts})
            if image_result.get("duplicate_found"):
                recommendations.append("Investigate duplicate image submission")
            if image_result.get("image_quality") == "blurry":
                recommendations.append("Request clearer product damage photos")

    # Video analysis
    if video_result:
        vid_pts = video_result.get("risk_points", 0)
        if vid_pts > 0:
            total_score += vid_pts
            for detail in video_result.get("details", []):
                breakdown.append({"factor": detail, "points": vid_pts})
            if video_result.get("repeated_frames_detected"):
                recommendations.append("Video appears to be static frames — request genuine video")

    # Invoice validation
    if has_invoice and invoice_result:
        inv_pts = invoice_result.get("risk_points", 0)
        if inv_pts > 0:
            total_score += inv_pts
            breakdown.append({
                "factor": "Invoice data mismatch with claim",
                "points": inv_pts
            })
            recommendations.append("Manually verify invoice against order records")

    # Behavioral: repeated refunds
    if recent_refund_count >= 3:
        pts = RISK_WEIGHTS["repeated_refund_requests"]
        total_score += pts
        breakdown.append({
            "factor": f"Customer has {recent_refund_count} refund requests in last 30 days",
            "points": pts
        })
        recommendations.append("Flag account for manual review — high refund frequency")
    elif recent_refund_count >= 2:
        pts = RISK_WEIGHTS["repeated_refund_requests"] // 2
        total_score += pts
        breakdown.append({
            "factor": f"Customer has {recent_refund_count} recent refund requests",
            "points": pts
        })

    # Cap at 100
    final_score = min(total_score, 100)
    risk_level = _get_risk_level(final_score)

    if not recommendations:
        recommendations.append("No immediate action required — standard processing")

    return {
        "risk_score": final_score,
        "risk_level": risk_level,
        "breakdown": breakdown,
        "recommendations": recommendations
    }
