"""
AI Refund Assistant (Feature 6)
Uses Gemini API if configured, otherwise rule-based fallback.
"""
import os
import re

GEMINI_AVAILABLE = False
try:
    import google.generativeai as genai
    _api_key = os.environ.get('GEMINI_API_KEY')
    if _api_key:
        genai.configure(api_key=_api_key)
        _gemini_model = genai.GenerativeModel('gemini-pro')
        GEMINI_AVAILABLE = True
except Exception:
    pass

SYSTEM_CONTEXT = """You are RefundIQ+ Assistant, a helpful AI for a refund fraud detection platform.
You help customers understand their refund status, risk scores, and rejection reasons.
Be concise, professional, and empathetic. Never share other users' data.
If asked about something unrelated to refunds, politely redirect."""


def _rule_based_response(message: str, context: dict) -> str:
    msg = message.lower()

    if any(w in msg for w in ['status', 'update', 'check']):
        s = context.get('status', 'unknown')
        return (f"Your refund #{context.get('refund_id','?')} is currently **{s}**. "
                + _status_explanation(s))

    if any(w in msg for w in ['risk', 'score', 'fraud']):
        score = context.get('risk_score', 'N/A')
        level = context.get('risk_level', 'N/A')
        return (f"Your refund has a risk score of **{score}/100** ({level}). "
                + _risk_explanation(score))

    if any(w in msg for w in ['reject', 'denied', 'why', 'reason']):
        reasons = context.get('factors', [])
        if reasons:
            items = '\n'.join(f"• {r['description']}" for r in reasons[:3])
            return f"Your refund was flagged due to:\n{items}\n\nIf you believe this is an error, please upload additional evidence."
        return "The rejection reasons are not available. Please contact support for details."

    if any(w in msg for w in ['appeal', 'dispute', 'wrong']):
        return ("To appeal a decision, log in to your dashboard and click on your refund request. "
                "You can upload additional evidence or contact our support team.")

    if any(w in msg for w in ['how long', 'when', 'time', 'days']):
        return ("Approved refunds are typically processed within 3–5 business days. "
                "Pending reviews are usually completed within 24–48 hours.")

    if any(w in msg for w in ['hello', 'hi', 'hey']):
        return "Hello! I'm your RefundIQ+ assistant. I can help you understand your refund status, risk score, or next steps. What would you like to know?"

    return ("I can help you with:\n"
            "• Checking your refund status\n"
            "• Understanding your risk score\n"
            "• Explaining rejection reasons\n"
            "• Guidance on appeals\n\n"
            "What would you like to know?")


def _status_explanation(status: str) -> str:
    explanations = {
        'pending': 'Our team is currently reviewing your submission.',
        'approved': 'Your refund has been approved and will be processed shortly.',
        'rejected': 'Unfortunately your claim was not approved. You may appeal with additional evidence.',
        'needs_evidence': 'Please log in and upload the requested additional documents.'
    }
    return explanations.get(status, '')


def _risk_explanation(score) -> str:
    try:
        s = int(score)
    except Exception:
        return ''
    if s <= 30:
        return 'This is a low risk score, meaning your claim appears genuine.'
    if s <= 60:
        return 'This is a medium risk score. Some aspects of your claim need manual review.'
    return 'This is a high risk score. Multiple fraud indicators were detected in your submission.'


def get_response(message: str, context: dict, history: list) -> str:
    """
    Get AI assistant response.
    context: dict with refund info (status, risk_score, risk_level, factors, etc.)
    history: list of {'role': 'user'|'assistant', 'content': str}
    """
    if GEMINI_AVAILABLE:
        try:
            ctx_str = ''
            if context:
                ctx_str = f"\nUser's refund context: {context}\n"
            hist_str = ''
            for h in history[-6:]:  # last 6 turns
                hist_str += f"{h['role'].capitalize()}: {h['content']}\n"

            prompt = f"{SYSTEM_CONTEXT}{ctx_str}\n{hist_str}User: {message}\nAssistant:"
            response = _gemini_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            pass  # fall through to rule-based

    return _rule_based_response(message, context)
