from flask import Flask, jsonify, request 
import mysql.connector
import os

import hashlib
import jwt
from datetime import datetime, timedelta
import boto3
from flask_cors import CORS
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
CORS(app) 

@app.route('/api/stream-audio/<int:book_id>/<chapter_title>')
def stream_audio(book_id, chapter_title):
    try:
        # Get the signed URL first
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT title FROM books WHERE id = %s", (book_id,))
        book = cursor.fetchone()
        cursor.close()
        db.close()
        
        if not book:
            return jsonify({"error": "Book not found"}), 404
        
        file_path = f"{book['title']}/{chapter_title}"
        signed_url = generate_signed_url(os.getenv('B2_BUCKET'), file_path)
        
        if not signed_url:
            return jsonify({"error": "Failed to generate URL"}), 500
        
        # Stream the audio from Backblaze through Flask
        response = requests.get(signed_url, stream=True)
        
        if response.status_code == 200:
            return response(
                response.iter_content(chunk_size=8192),
                content_type=response.headers.get('content-type', 'audio/mpeg'),
                headers={
                    'Cache-Control': 'no-cache',
                    'Access-Control-Allow-Origin': '*'
                }
            )
        else:
            return jsonify({"error": f"Audio not found: {response.status_code}"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

# def generate_signed_url(bucket_name, file_path, expiration=3600):
#     """Generate a signed URL for private Backblaze B2 files"""
#     s3 = boto3.client(
#         's3',
#         endpoint_url=os.getenv('B2_ENDPOINT'),
#         aws_access_key_id=os.getenv('B2_KEY_ID'),
#         aws_secret_access_key=os.getenv('B2_APP_KEY')
#     )
    
#     try:
#         url = s3.generate_presigned_url(
#             'get_object',
#             Params={'Bucket': bucket_name, 'Key': file_path},
#             ExpiresIn=expiration
#         )
#         return url
#     except Exception as e:
#         print(f"Error generating signed URL: {str(e)}")
#         return None

# Add this endpoint to your Flask app
@app.route('/api/audio-url/<int:book_id>/<chapter_title>')
def get_audio_url(book_id, chapter_title):
    try:
        # The chapter_title is now automatically URL decoded by Flask
        # No need to urllib.parse.unquote() it
    
        # Get book title from database
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT title FROM books WHERE id = %s", (book_id,))
        book = cursor.fetchone()
        cursor.close()
        db.close()
        
        if not book:
            return jsonify({"error": "Book not found"}), 404
        
        # Generate signed URL
        file_path = f"{book['title']}/{chapter_title}"
        signed_url = generate_signed_url(
            os.getenv('B2_BUCKET'),
            file_path,
            expiration=3600  # 1 hour expiry
        )
        
        if signed_url:
            return jsonify({"url": signed_url})
        else:
            return jsonify({"error": "Failed to generate audio URL"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500



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

def backblaze_store():
    try:
        return boto3.client(
            's3',
            endpoint_url=os.getenv('B2_ENDPOINT'),
            aws_access_key_id=os.getenv('B2_KEY_ID'),
            aws_secret_access_key=os.getenv('B2_APP_KEY'),
            region_name='us-east-005'
        )
    except Exception as e:
        print(f"❌ Backblaze B2 connection failed: {str(e)}")
        return False

@app.route('/', methods=['GET'])
def home():
    """Root endpoint that returns basic info or redirects"""
    return jsonify({
        "message": "Library API",
        "endpoints": {
            "login": "POST /",
            "register": "POST /api/register", 
            "books": "GET /books",
            "health": "GET /health"
        }
    })



@app.route('/', methods=['POST'])
# @app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"success": False, "error": "Email and password required"}), 400
        
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id, name, email, role FROM users WHERE email = %s AND password = %s", 
                      (email, hashed_password))
        user = cursor.fetchone()
        cursor.close()
        db.close()
        
        if user:
            token = jwt.encode({
                'user_id': user['id'],
                'email': user['email'],
                'role': user['role'],
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, os.getenv('JWT_SECRET', 'fallback-secret'), algorithm='HS256')
            
            return jsonify({
                "success": True,
                "user": user,
                "token": token
            })
        else:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/register', methods=['POST'])
def api_register():
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        membership_number = data.get('membership_number')
        
        # Validation
        if not all([name, email, password]):
            return jsonify({"success": False, "error": "Name, email, and password are required"}), 400
        
        # Email validation
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({"success": False, "error": "Invalid email format"}), 400
        
        # Password length check
        if len(password) < 6:
            return jsonify({"success": False, "error": "Password must be at least 6 characters"}), 400
        
        # Hash password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        db = get_db()
        if not db:
            return jsonify({"success": False, "error": "Database connection failed"}), 500
        
        cursor = db.cursor()
        
        try:
            # Check if email already exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return jsonify({"success": False, "error": "Email already exists"}), 409
            
            # Insert new user
            cursor.execute("""
                INSERT INTO users (name, email, password, membership_number, role)
                VALUES (%s, %s, %s, %s, 'member')
            """, (name, email, hashed_password, membership_number))
            
            db.commit()
            user_id = cursor.lastrowid
            
            # Generate token for auto-login
            token = jwt.encode({
                'user_id': user_id,
                'email': email,
                'role': 'member',
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, os.getenv('JWT_SECRET', 'fallback-secret'), algorithm='HS256')
            
            return jsonify({
                "success": True,
                "message": "Registration successful",
                "user": {
                    "id": user_id,
                    "name": name,
                    "email": email,
                    "role": "member",
                    "membership_number": membership_number
                },
                "token": token
            })
            
        except mysql.connector.IntegrityError as e:
            db.rollback()
            if "Duplicate entry" in str(e):
                return jsonify({"success": False, "error": "Email or membership number already exists"}), 409
            return jsonify({"success": False, "error": "Database integrity error"}), 400
            
        except Exception as e:
            db.rollback()
            return jsonify({"success": False, "error": f"Registration failed: {str(e)}"}), 500
            
        finally:
            cursor.close()
            db.close()
            
    except Exception as e:
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500
    


@app.route('/books', methods=['GET'])
def get_books():
    try:
        db = get_db()
        if db is None:
            return jsonify({"error": "Database connection failed"}), 500
            # return jsonify({"error": "DB connection failed", "env": dict(os.environ)}), 500
        
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
                    SELECT 
                        b.id as book_id,
                        b.title as book_title,
                        c.id as chapter_id,
                        c.chapter_number,
                        c.title as chapter_title
                    FROM books b
                    INNER JOIN chapters c ON b.id = c.book_id 
                    ORDER BY b.title, c.chapter_number
                    LIMIT 10
                """)
        results = cursor.fetchall()

        books = {}
        for row in results:
            book_id = row['book_id']
            if book_id not in books:
                books[book_id] = {
                    'id': book_id,
                    'title': row['book_title'],
                    'chapters': []
                }
            
            if row['chapter_id']:  # Only add if chapter exists
                books[book_id]['chapters'].append({
                    'title': row['chapter_title'],
                    'id': row['chapter_id'],
                    'chapter_number': row['chapter_number']
                })
        
        return jsonify({"books": list(books.values())})

        # response = jsonify({"books": books})
        # response.headers["Cache-Control"] = "public, max-age=3600"  # 1 hour cache
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
    
    # try:
    #     file_name = os.path.basename(file_path)
    #     B2_BUCKET = os.getenv('B2_BUCKET')
    #     s3.upload_file(file_path, B2_BUCKET, file_name)
    #     print(f"Successfully uploaded {file_name} to {B2_BUCKET}")
    #     return True
    # except Exception as e:
    #     print(f"Upload failed: {str(e)}")
    #     return False

    # # Test upload
    # file_path = r"E:\Books-Audible\The Girl in Room 105 (Hindi)\Chapter 05.mp3"
    
    # # Verify file exists first
    # if not os.path.exists(file_path):
    #     print(f"Error: File not found at {file_path}")
    # else:
    #     if upload_to_b2(file_path):
    #         print("Starting Flask server...")
    #         app.run(host="0.0.0.0", port=8000)

def test_b2_connection():
    """Test if Backblaze B2 credentials work"""
    try:
        s3 = backblaze_store()
        print("✅ Connected to Backblaze B2 successfully!")
        
        # Test bucket access directly (skip list_buckets)
        try:
            s3.head_bucket(Bucket=os.getenv('B2_BUCKET'))
            print(f"✅ Access to bucket '{os.getenv('B2_BUCKET')}' confirmed!")
            
            # Test if we can list objects in the bucket
            try:
                response = s3.list_objects_v2(
                    Bucket=os.getenv('B2_BUCKET'),
                    MaxKeys=5  # Limit to first 5 objects
                )
                print(f"✅ Can list objects in bucket")
                if 'Contents' in response:
                    print("Sample files in bucket:")
                    for obj in response['Contents'][:3]:  # Show first 3 files
                        print(f"  - {obj['Key']} ({obj['Size']} bytes)")
                return True
            except Exception as list_error:
                print(f"❌ Cannot list objects: {str(list_error)}")
                return False
                
        except Exception as e:
            print(f"❌ Cannot access bucket: {str(e)}")
            return False
            
    except Exception as e:
        print(f"❌ Backblaze B2 connection failed: {str(e)}")
        return False

# def test_b2_simple():
#     """Simple test to check basic connectivity"""
#     try:
#         s3 = boto3.client(
#             's3',
#             endpoint_url=os.getenv('B2_ENDPOINT'),
#             aws_access_key_id=os.getenv('B2_KEY_ID'),
#             aws_secret_access_key=os.getenv('B2_APP_KEY'),
#             region_name='us-east-005'
#         )
        
#         # Try a simple operation that doesn't require list permissions
#         try:
#             # Check if we can access a specific file
#             s3.head_object(
#                 Bucket=os.getenv('B2_BUCKET'),
#                 Key="BHARAT NA 75 FILM UDHYOGNA SITARO/Chapter 01.mp3"
#             )
#             print("✅ Can access specific file!")
#             return True
#         except Exception as e:
#             print(f"File access error: {str(e)}")
#             return False
            
    # except Exception as e:
    #     print(f"B2 connection failed: {str(e)}")
    #     return False

def generate_signed_url(bucket_name, file_path, expiration=3600):
    """Generate a signed URL for private Backblaze B2 files"""
    try:
        s3 = backblaze_store()
        
        url = s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name, 
                'Key': file_path
            },
            ExpiresIn=expiration,
            HttpMethod='GET'  # Explicitly specify GET
        )
        return url
    except Exception as e:
        print(f"Error generating signed URL: {str(e)}")
        return None


import requests

if __name__ == "__main__":
    print("Testing database connection...")
    
    test_db = get_db()
    if test_db:
        print("✅ Connected to Railway Database successful!")
        test_db.close()
    else:
        print("❌ Railway Database connection failed - check credentials")

    test_b2_connection()
    # print("\nTesting Backblaze B2 connection...")
    # test_b2_simple()

    # # Test signed URL generation
    # print("\nTesting signed URL generation...")
    
    # signed_url = generate_signed_url(
    #     os.getenv('B2_BUCKET'),
    #     "BHARAT NA 75 FILM UDHYOGNA SITARO/Chapter 01.mp3"
    # )
    
    # if signed_url:
    #     print(f"Signed URL: {signed_url}")

    #     try:
    #         # Use GET instead of HEAD for testing
    #         response = requests.get(signed_url, timeout=10, stream=True)
    #         if response.status_code == 200:
    #             print("✅ Signed URL works!")
    #             print(f"Content-Type: {response.headers.get('content-type')}")
    #             print(f"Content-Length: {response.headers.get('content-length')} bytes")
    #         else:
    #             print(f"❌ Signed URL failed with status: {response.status_code}")
    #             print(f"Response headers: {dict(response.headers)}")
    #     except Exception as e:
    #         print(f"❌ Signed URL test failed: {str(e)}")
    # else:
    #     print("❌ Failed to generate signed URL")

    app.run(host="0.0.0.0", port=8000)