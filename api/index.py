# api/index.py
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "API is working!"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

# Vercel handler
def handler(request):
    with app.app_context():
        # Simple handler that returns JSON
        path = request.path
        if path == '/':
            return {'statusCode': 200, 'body': '{"message": "API is working!"}'}
        elif path == '/health':
            return {'statusCode': 200, 'body': '{"status": "healthy"}'}
        else:
            return {'statusCode': 404, 'body': '{"error": "Not found"}'}
