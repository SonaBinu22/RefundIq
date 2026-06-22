import sys
import os

# Ensure the venv site-packages are on the path
venv_site = os.path.join(os.path.dirname(__file__), '.venv', 'Lib', 'site-packages')
if os.path.exists(venv_site) and venv_site not in sys.path:
    sys.path.insert(0, venv_site)

from backend import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
