from datetime import datetime
from .db import db

# Role hierarchy: customer < moderator < admin < superadmin
ROLES = ['customer', 'moderator', 'admin', 'superadmin']

PERMISSIONS = {
    'customer':   ['submit_refund', 'view_own_refunds', 'use_chat'],
    'moderator':  ['submit_refund', 'view_own_refunds', 'use_chat', 'review_refunds', 'view_all_refunds'],
    'admin':      ['submit_refund', 'view_own_refunds', 'use_chat', 'review_refunds',
                   'view_all_refunds', 'approve_refunds', 'view_analytics', 'view_audit'],
    'superadmin': ['*'],  # all permissions
}


class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='customer')

    # Account security
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    password_history = db.Column(db.Text, default='[]')   # JSON list of last 5 hashes
    last_login = db.Column(db.DateTime, nullable=True)
    password_reset_token = db.Column(db.String(100), nullable=True)
    password_reset_expires = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    refunds = db.relationship('RefundRequest', backref='user', lazy=True)

    def is_locked(self):
        if self.locked_until and datetime.utcnow() < self.locked_until:
            return True
        return False

    def has_permission(self, perm):
        role_perms = PERMISSIONS.get(self.role, [])
        return '*' in role_perms or perm in role_perms

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'is_locked': self.is_locked(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat()
        }
