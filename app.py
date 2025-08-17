from flask import Flask, jsonify, request 
import mysql.connector
import os
#import boto3
#import base as b  

from dotenv import load_dotenv

#from serverless_wsgi import handle_request

load_dotenv()  # Load .env file for local development

# def handler(event, context):
#     return handle_request(app, event, context)


# from sqlalchemy import create_engine
# import psycopg2

# engine = create_engine(b.postgresql_DATABASE_URL)

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "db": "ok" if get_db() else "down"})

    
@app.route('/debug')
def debug():
    X_AUTH_SECRET = os.getenv('X_AUTH_SECRET')
    if not X_AUTH_SECRET:
        raise ValueError("Missing X_AUTH_SECRET in .env file")
    
    if not request.headers.get('X-Auth') == os.getenv('X_AUTH_SECRET'):
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({
        "db_status": "Connected" if get_db() else "Failed",
        "env_vars": {k:v for k,v in os.environ.items() if k.startswith('DB_')}
    })


# @app.route('/books')
# def get_books():
#     conn = engine.connect()
#     books = conn.execute("SELECT * FROM books LIMIT 10").fetchall()
#     return jsonify([dict(book) for book in books])


# Database - Railway MySQL connection
def get_db():
    try:
        return mysql.connector.connect(
            host=os.getenv('DB_HOST'),  # Get from environment
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            port=int(os.getenv('DB_PORT'))  # Default to 3306 if not set
        )
    except Exception as e:
        print(f"DB Error: {str(e)}")
        return None
    

@app.route('/')
def home():
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Database connection failed"}), 500
            # return jsonify({"error": "DB connection failed", "env": dict(os.environ)}), 500
        
        cursor = db.cursor(dictionary=True)
        # cursor.execute("SELECT 1")  # Simple test query first
        # cursor.fetchall()

        cursor.execute("SELECT * FROM books LIMIT 10")
        books = cursor.fetchall()

        response = jsonify({"books": books})
        response.headers["Cache-Control"] = "public, max-age=3600"  # 1 hour cache
        return response
        # return jsonify({"books": books})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'db' in locals(): db.close()

# Storage - Backblaze connection
# def upload_to_b2(file_path):
#     s3 = boto3.client(
#         's3',
#         endpoint_url=os.getenv('B2_ENDPOINT'),
#         aws_access_key_id=os.getenv('B2_KEY_ID'),
#         aws_secret_access_key=os.getenv('B2_APP_KEY')
#     )
    
#     try:
#         file_name = os.path.basename(file_path)
#         B2_BUCKET = os.getenv('B2_BUCKET')
#         s3.upload_file(file_path, B2_BUCKET, file_name)
#         print(f"Successfully uploaded {file_name} to {B2_BUCKET}")
#         return True
#     except Exception as e:
#         print(f"Upload failed: {str(e)}")
#         return False

if __name__ == "__main__":

    print("Testing database connection...")
    test_db = get_db()
    if test_db:
        print("✅ Database connection successful!")
        test_db.close()
    else:
        print("❌ Database connection failed - check credentials")

    # # Test upload
    # file_path = r"E:\Books-Audible\The Girl in Room 105 (Hindi)\Chapter 05.mp3"
    
    # # Verify file exists first
    # if not os.path.exists(file_path):
    #     print(f"Error: File not found at {file_path}")
    # else:
    #     if upload_to_b2(file_path):
    #         print("Starting Flask server...")
    #         app.run(host="0.0.0.0", port=8000)

    app.run(host="0.0.0.0", port=8000)
    


