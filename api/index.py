# api/index.py
from http import HTTPStatus
import json

def handler(request, context):
    """Vercel serverless function handler - MUST use this exact signature"""
    try:
        path = request.path
        method = request.method
        
        # Handle different routes
        if path == '/' and method == 'GET':
            return {
                'statusCode': HTTPStatus.OK,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    "message": "Library API is working!",
                    "endpoints": {
                        "health": "GET /api/health",
                        "login": "POST /api/login", 
                        "register": "POST /api/register",
                        "books": "GET /api/books"
                    }
                })
            }
            
        elif path == '/api/health' and method == 'GET':
            return {
                'statusCode': HTTPStatus.OK,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"status": "healthy", "message": "API is running"})
            }
            
        elif path == '/api/login' and method == 'POST':
            # Simple login response
            return {
                'statusCode': HTTPStatus.OK,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"success": True, "message": "Login endpoint"})
            }
            
        else:
            return {
                'statusCode': HTTPStatus.NOT_FOUND,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"error": "Endpoint not found", "path": path})
            }
            
    except Exception as e:
        return {
            'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": str(e)})
        }
