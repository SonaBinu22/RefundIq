import sys
import os

# Ensure venv packages are available
venv_site = os.path.join(os.path.dirname(__file__), '.venv', 'Lib', 'site-packages')
if os.path.exists(venv_site) and venv_site not in sys.path:
    sys.path.insert(0, venv_site)

from backend import create_app
from backend.realtime import socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True, use_reloader=False, host='0.0.0.0', port=5000)
