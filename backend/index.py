# backend/api/index.py
from ..app import app

def handler(request):
    with app.app_context():
        return app(request)