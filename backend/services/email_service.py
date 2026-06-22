"""
Email Notification Service (Feature 5)
Sends HTML emails for key refund events.
Gracefully skips if Flask-Mail is not configured.
"""
from flask import current_app, render_template_string

_MAIL_AVAILABLE = False
try:
    from flask_mail import Mail, Message
    _MAIL_AVAILABLE = True
except ImportError:
    pass

mail = None


def init_mail(app):
    global mail, _MAIL_AVAILABLE
    if _MAIL_AVAILABLE:
        mail = Mail(app)


def _send(to: str, subject: str, html: str):
    if not mail:
        current_app.logger.info(f'[EMAIL SKIP] To: {to} | Subject: {subject}')
        return
    try:
        msg = Message(subject, recipients=[to], html=html,
                      sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@refundiq.com'))
        mail.send(msg)
    except Exception as e:
        current_app.logger.warning(f'Email send failed: {e}')


def _base_template(title: str, body: str, color: str = '#007bff') -> str:
    return f"""
    <div style="font-family:Segoe UI,sans-serif;max-width:560px;margin:auto;border:1px solid #eee;border-radius:12px;overflow:hidden">
      <div style="background:{color};padding:24px 30px">
        <h2 style="color:#fff;margin:0">RefundIQ+</h2>
        <p style="color:rgba(255,255,255,.8);margin:6px 0 0">{title}</p>
      </div>
      <div style="padding:28px 30px;color:#333">{body}</div>
      <div style="padding:16px 30px;background:#f8f9fa;font-size:12px;color:#aaa">
        This is an automated message from RefundIQ+. Do not reply.
      </div>
    </div>"""


def send_refund_submitted(user_email: str, user_name: str, refund_id: int, product: str, risk_level: str):
    color = '#e74c3c' if risk_level == 'High Risk' else '#f39c12' if risk_level == 'Medium Risk' else '#27ae60'
    body = f"""
    <p>Hi <strong>{user_name}</strong>,</p>
    <p>Your refund request <strong>#{refund_id}</strong> for <strong>{product}</strong> has been received.</p>
    <p>Risk Level: <span style="color:{color};font-weight:600">{risk_level}</span></p>
    <p>We will review your request and notify you of the outcome.</p>"""
    _send(user_email, f'Refund Request #{refund_id} Received – RefundIQ+',
          _base_template('Refund Submitted', body))


def send_refund_approved(user_email: str, user_name: str, refund_id: int, product: str):
    body = f"""
    <p>Hi <strong>{user_name}</strong>,</p>
    <p>Great news! Your refund request <strong>#{refund_id}</strong> for <strong>{product}</strong>
    has been <span style="color:#27ae60;font-weight:600">approved</span>.</p>
    <p>The refund will be processed within 3-5 business days.</p>"""
    _send(user_email, f'Refund #{refund_id} Approved – RefundIQ+',
          _base_template('Refund Approved ✓', body, '#27ae60'))


def send_refund_rejected(user_email: str, user_name: str, refund_id: int, product: str, reason: str = None):
    reason_block = f'<p><strong>Reason:</strong> {reason}</p>' if reason else ''
    body = f"""
    <p>Hi <strong>{user_name}</strong>,</p>
    <p>Your refund request <strong>#{refund_id}</strong> for <strong>{product}</strong>
    has been <span style="color:#e74c3c;font-weight:600">rejected</span>.</p>
    {reason_block}
    <p>If you believe this is an error, please contact support.</p>"""
    _send(user_email, f'Refund #{refund_id} Rejected – RefundIQ+',
          _base_template('Refund Rejected', body, '#e74c3c'))


def send_evidence_requested(user_email: str, user_name: str, refund_id: int, notes: str = None):
    notes_block = f'<p><strong>Admin notes:</strong> {notes}</p>' if notes else ''
    body = f"""
    <p>Hi <strong>{user_name}</strong>,</p>
    <p>Additional evidence is required for your refund request <strong>#{refund_id}</strong>.</p>
    {notes_block}
    <p>Please log in and upload the required documents.</p>"""
    _send(user_email, f'Additional Evidence Required – Refund #{refund_id}',
          _base_template('Evidence Required', body, '#f39c12'))


def send_password_changed(user_email: str, user_name: str):
    body = f"""
    <p>Hi <strong>{user_name}</strong>,</p>
    <p>Your RefundIQ+ account password was changed successfully.</p>
    <p>If you did not make this change, contact support immediately.</p>"""
    _send(user_email, 'Password Changed – RefundIQ+',
          _base_template('Password Changed', body, '#6c757d'))


def send_account_locked(user_email: str, user_name: str, minutes: int = 15):
    body = f"""
    <p>Hi <strong>{user_name}</strong>,</p>
    <p>Your account has been <strong>temporarily locked</strong> for {minutes} minutes
    due to multiple failed login attempts.</p>
    <p>It will unlock automatically. If this was not you, reset your password immediately.</p>"""
    _send(user_email, 'Account Locked – RefundIQ+',
          _base_template('Account Locked ⚠️', body, '#e74c3c'))
