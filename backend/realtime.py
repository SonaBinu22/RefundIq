"""
Real-Time Notifications via Flask-SocketIO (Feature 15)
"""
from flask_socketio import SocketIO, emit, join_room

socketio = SocketIO(cors_allowed_origins='*', async_mode='threading')


def init_socketio(app):
    socketio.init_app(app)


@socketio.on('join')
def on_join(data):
    """Client joins a room: 'admin' or 'user_<id>'"""
    room = data.get('room')
    if room:
        join_room(room)


def notify_new_refund(refund_id: int, product: str, risk_level: str, risk_score: int):
    socketio.emit('new_refund', {
        'refund_id': refund_id, 'product': product,
        'risk_level': risk_level, 'risk_score': risk_score
    }, room='admin')


def notify_decision(user_id: int, refund_id: int, status: str, product: str):
    socketio.emit('refund_decision', {
        'refund_id': refund_id, 'status': status, 'product': product
    }, room=f'user_{user_id}')
