# api/index.py
from http import HTTPStatus
import json

def handler(request, context):
    """Vercel serverless function handler"""
    try:
        path = request.path
        method = request.method
        
        if path == '/' and method == 'GET':
            return {
                'statusCode': HTTPStatus.OK,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    "message": "Library API",
                    "endpoints": {
                        "health": "GET /health",
                        "login": "POST /api/login",
                        "register": "POST /api/register"
                    }
                })
            }
            
        elif path == '/health' and method == 'GET':
            return {
                'statusCode': HTTPStatus.OK,
                'body': json.dumps({"status": "healthy"})
            }
            
        else:
            return {
                'statusCode': HTTPStatus.NOT_FOUND,
                'body': json.dumps({"error": "Endpoint not found"})
            }
            
    except Exception as e:
        return {
            'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
            'body': json.dumps({"error": str(e)})
        }