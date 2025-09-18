# api/index.py
from flask import Flask, jsonify
import json

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "Library API",
        "endpoints": {
            "health": "GET /api/health",
            "login": "POST /api/login",
            "register": "POST /api/register"
        }
    })

@app.route('/api/health')
def health():
    return jsonify({"status": "healthy"})

# Vercel-compatible handler
def handler(request, context):
    """This is the signature Vercel expects"""
    path = request.path
    method = request.method
    
    if path == '/' and method == 'GET':
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"message": "API is working!"})
        }
    elif path == '/api/health' and method == 'GET':
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"status": "healthy"})
        }
    else:
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": "Not found"})
        }
