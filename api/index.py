# api/index.py
import json

def handler(request, context):
    """Minimal working handler for Vercel"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            "success": True,
            "message": "API deployed successfully!",
            "endpoint": request.path
        })
    }
