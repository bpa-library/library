
# app.py
########
from flask import Flask, jsonify, request 
# import mysql.connector
import os

import hashlib
import jwt
from datetime import datetime, timedelta
# import boto3
from flask_cors import CORS
import base as b
import storage as s
# from storage import backblaze_store
import math
from datetime import datetime, timezone, timedelta  #
import re

# def handler(event, context):
#     return handle_request(app, event, context)

DB_TYPE = os.getenv('DB_TYPE').lower()   # MySQL / postgreSQL

# PostgreSQL - Free Forever - https://neon.com/ - (Neon.tech)
# Free Limit 3GB storage, Beyond Free $0.10/GB
# from sqlalchemy import create_engine, text
# import psycopg2


app = Flask(__name__)
CORS(app) 

bz = s.backblaze_store()
###################
from functools import wraps
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Token required"}), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            decoded = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
            
            # Check if user is admin using the existing role column
            user = b.universal_db_select(
                "SELECT id, role FROM users WHERE id = %s", 
                (decoded['user_id'],)
            )
            
            if not user or user[0]['role'] != 'admin':
                return jsonify({"error": "Admin access required"}), 403
                
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        except Exception as e:
            return jsonify({"error": "Token verification failed"}), 401
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/verify-token', methods=['POST'])
def verify_token():
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({"valid": False, "error": "Token required"}), 400
        
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        try:
            decoded = jwt.decode(
                token, 
                os.getenv('JWT_SECRET', 'fallback-secret'), 
                algorithms=['HS256']
            )
            
            # Check if token is expired
            exp_timestamp = decoded.get('exp')
            if exp_timestamp and datetime.now(timezone.utc).timestamp() > exp_timestamp:
                return jsonify({"valid": False, "error": "Token expired"}), 401
            
            # Get user info from database
            user = b.universal_db_select(
                "SELECT id, name, email, role FROM users WHERE id = %s", 
                (decoded['user_id'],)
            )
            
            if not user:
                return jsonify({"valid": False, "error": "User not found"}), 401
            
            return jsonify({
                "valid": True,
                "user": user[0],
                "expires_in": exp_timestamp - datetime.now(timezone.utc).timestamp() if exp_timestamp else None
            })
            
        except jwt.ExpiredSignatureError:
            return jsonify({"valid": False, "error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"valid": False, "error": "Invalid token"}), 401
            
    except Exception as e:
        return jsonify({"valid": False, "error": str(e)}), 500
###################


################### Book Management - F
@app.route('/admin/books', methods=['POST'])
@admin_required
def add_book():
    try:
        data = request.get_json()
        query = """
            INSERT INTO books (title, author, publisher, isbn, description, category_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        result = b.db_insert (query, (
            data['title'], data['author'], data['publisher'], 
            data['isbn'], data['description'], data['category_id']
        ))
        
        return jsonify({"book_id": result, "message": "Book added successfully"}), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
################### Book Management

################### upload
@app.route('/api/upload_audio', methods=['POST'])
def api_upload_audio():
    try:
        book_id = request.form.get("book_id")
        file = request.files.get("file")

        if not book_id or not file:
            return jsonify({"success": False, "error": "Missing book_id or file"}), 400
        
        chapter_number = extract_chapter_number(file.filename)
        if chapter_number is None:
            # skip inserting into chapters
            return jsonify({
                "success": True,
                "file_path": file.filename,
                # "file_path": file_path,
                "note": "Uploaded non-chapter audio (not saved in DB)"
            }), 200

        # Get book details
        book = b.universal_db_select("SELECT title, author FROM books WHERE id = %s", (book_id,))
        if not book:
            return jsonify({"success": False, "error": "Book not found"}), 404
        book = book[0]

        folder_name = f"{book['title']} By {book['author']}"
        file_path = f"{folder_name}/{file.filename}"

        # Upload to Backblaze
        # s3 = s.backblaze_store()
        bucket = os.getenv("B2_BUCKET")
        bz.upload_fileobj(file, bucket, file_path, ExtraArgs={'ContentType': 'audio/mpeg'})
        # s3.upload_fileobj(file, bucket, file_path, ExtraArgs={'ContentType': 'audio/mpeg'})

        # Insert into chapters
        # chapter_number = extract_chapter_number(file.filename)
        
        query = "INSERT INTO chapters (book_id, title, chapter_number) VALUES (%s, %s, %s)"
        b.db_insert(query, (book_id, file.filename, chapter_number))

        return jsonify({"success": True, "file_path": file_path}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def extract_chapter_number(filename):
    """Extract chapter number from filename"""
    try:
        # Patterns: "aud001.mp3", "chapter01.mp3", "001.mp3", etc.

        import re
        name = filename.lower()

        # Allow formats like aud001.mp3, chapter01.mp3, 001.mp3
        match = re.match(r'^(?:aud|chapter)?0*(\d+)\.mp3$', name)
        if match:
            return int(match.group(1))

        # If no valid match → skip
        return None

        # import re
        # numbers = re.findall(r'\d+', filename)
        # if numbers:
        #     return int(numbers[0])
        # return 1  # Default to chapter 1 if no number found
    except:
        return 1

@app.route('/api/get_all_books', methods=['GET'])
#@admin_required
def api_get_all_books():
    try:
        books = b.universal_db_select("SELECT id, title, author FROM books ORDER BY title")
        return jsonify({"success": True, "books": books if books else []}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
################### upload

################### Book Management - F
@app.route('/api/get_book', methods=['GET'])
def api_get_book():
    """Get single book details by ID"""
    try:
        book_id = request.args.get("book_id", type=int)
        if not book_id:
            return jsonify({"success": False, "error": "book_id required"}), 400

        query = "SELECT id, title, author FROM books WHERE id = %s"
        book = b.universal_db_select(query, (book_id,))
        
        if not book:
            return jsonify({"success": False, "error": "Book not found"}), 404

        return jsonify({"success": True, "book": book[0]}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
###################

################### admin_users.py
@app.route('/admin/users', methods=['GET'])
@admin_required
def get_users():
    try:
        search = request.args.get('search', '')
        role_filter = request.args.get('role', '')
        
        query = "SELECT id, name, email, role, membership_number FROM users WHERE 1=1"
        params = []
        
        if search:
            query += " AND (name LIKE %s OR email LIKE %s)"
            params.extend([f'%{search}%', f'%{search}%'])
        
        if role_filter and role_filter != 'All':
            query += " AND role = %s"
            params.append(role_filter)
        
        query += " ORDER BY name"
        
        users = b.universal_db_select(query, params)
        
        return jsonify({
            "success": True,
            "users": users
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
###################

###################
@app.route('/admin/users/<int:user_id>/role', methods=['PUT'])
@admin_required
def update_user_role(user_id):
    try:
        data = request.get_json()
        new_role = data.get('role')
        
        if new_role not in ['member', 'admin']:
            return jsonify({"success": False, "error": "Invalid role"}), 400
        
        result = b.db_update(
            "UPDATE users SET role = %s WHERE id = %s",
            (new_role, user_id)
        )
        
        if result:
            return jsonify({"success": True, "message": "User role updated"})
        else:
            return jsonify({"success": False, "error": "User not found"}), 404
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
###################

@app.route('/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    try:
        # Prevent admin from deleting themselves
        token = request.headers.get('Authorization', '')
        if token.startswith('Bearer '):
                token = token[7:]
        decoded = jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])

        current_user_id = decoded['user_id']
        if user_id == current_user_id:
            return jsonify({"success": False, "error": "Cannot delete your own account"}), 400
        
        result = b.db_execute (
            "DELETE FROM users WHERE id = %s", (user_id,)
        )
        
        if result:
            return jsonify({"success": True, "message": "User deleted successfully"})
        else:
            return jsonify({"success": False, "error": "User not found"}), 404
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/users/analytics', methods=['GET'])
@admin_required
def get_user_analytics():
    try:
        # Get total user count
        total_users = b.universal_db_select("SELECT COUNT(*) as count FROM users")[0]['count']
        
        # Get users by role
        role_counts = b.universal_db_select(
            "SELECT role, COUNT(*) as count FROM users GROUP BY role"
        )
        
        # Get recent signups (last 30 days)
        recent_signups = b.universal_db_select(
            "SELECT COUNT(*) as count FROM users WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)"
        )[0]['count']
        
        # Convert role counts to dictionary
        role_dict = {item['role']: item['count'] for item in role_counts}
        
        analytics = {
            'total_users': total_users,
            'admin_count': role_dict.get('admin', 0),
            'member_count': role_dict.get('member', 0),
            'recent_signups': recent_signups
        }
        
        return jsonify({
            "success": True,
            "analytics": analytics
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

###################


###################
@app.route("/api/get-total-books", methods=["GET"])
def api_get_total_books():
    try:
        result = b.universal_db_select("SELECT COUNT(1) as count FROM books")
        count = result[0]['count'] if result else 0
        return jsonify({"success": True, "count": count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
###################

###################
@app.route("/api/get-total-users", methods=["GET"])
def api_get_total_users():
    try:
        result = b.universal_db_select("SELECT COUNT(1) as count FROM users")
        count = result[0]['count'] if result else 0
        return jsonify({"success": True, "count": count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
###################
###################
@app.route("/api/get-total-chapters", methods=["GET"])
def api_get_total_chapters():
    try:
        result = b.universal_db_select("SELECT COUNT(1) as count FROM chapters")
        count = result[0]['count'] if result else 0
        return jsonify({"success": True, "count": count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

###################

###################
def check_database_status():
    try:
        result = b.universal_db_select("SELECT 1 as test")
        return result is not None
    except:
        return False
    
@app.route('/api/check_database_status', methods=['GET'])
def api_check_database_status():
    status = check_database_status()
    return jsonify({"database_connected": status})
###################

###################
@app.route('/api/check_backblaze_status', methods=['GET'])
def api_check_backblaze_status():
    status = True if bz else '❌ Disconnected'
    return jsonify({"backblaze_connected": status })
###################  

################### admin_dashboard.py
@app.route("/api/get-storage-usage", methods=["GET"])
def api_get_storage_usage():
    try:
        # s3 = s.backblaze_store()
        s3 = bz
        bucket_name = os.getenv("B2_BUCKET")
        if not s3 or not bucket_name:
            return jsonify({"success": False, "error": "Storage not configured"}), 500

        total_size = 0
        continuation_token = None

        while True:
            if continuation_token:
                resp = s3.list_objects_v2(Bucket=bucket_name, ContinuationToken=continuation_token)
            else:
                resp = s3.list_objects_v2(Bucket=bucket_name)

            for obj in resp.get("Contents", []):
                total_size += obj["Size"]

            if resp.get("IsTruncated"):
                continuation_token = resp.get("NextContinuationToken")
            else:
                break

        quota_gb = float(os.getenv("B2_STORAGE_QUOTA_GB", "10"))
        used_gb = round(total_size / (1024**3), 2)
        usage_ratio = min(used_gb / quota_gb, 1.0)

        return jsonify({
            "success": True,
            "used_gb": used_gb,
            "quota_gb": quota_gb,
            "usage_ratio": usage_ratio
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
################### admin_dashboard.py


@app.route('/api/audio-url/<int:book_id>/<path:chapter_title>')
def get_audio_url(book_id, chapter_title):
    try:
        book_result = b.universal_db_select("SELECT title, author FROM books WHERE id = %s", (book_id,))
        if not book_result or len(book_result) == 0:
            return jsonify({"error": "Book not found"}), 404
        
        book = book_result[0]

        folder_name = f"{book['title']} By {book['author']}"
        file_path = f"{folder_name}/{chapter_title}"

        import urllib.parse
        file_path = urllib.parse.unquote(file_path)

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



@app.route('/health')
def health():
    return jsonify({"status": "healthy", "db": "ok" if b.MySQL_db() else "down"})
    
@app.route('/debug')
def debug():
    X_AUTH_SECRET = os.getenv('X_AUTH_SECRET')
    if not X_AUTH_SECRET:
        raise ValueError("Missing X_AUTH_SECRET in .env file")
    
    if not request.headers.get('X-Auth') == os.getenv('X_AUTH_SECRET'):
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({
        "db_status": "Connected" if b.MySQL_db() else "Failed",
        "env_vars": {k:v for k,v in os.environ.items() if k.startswith('DB_')}
    })



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


# @app.route('/', methods=['POST'])
@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"success": False, "error": "Email and password required"}), 400
        
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        user = b.universal_db_select("SELECT id, name, email, role FROM users WHERE email = %s AND password = %s", 
                      (email, hashed_password))
        # db = MySQL_db()
        # cursor = db.cursor(dictionary=True)
        # cursor.execute("SELECT id, name, email, role FROM users WHERE email = %s AND password = %s", 
        #               (email, hashed_password))
        # user = cursor.fetchone()
        # cursor.close()
        # db.close()
        
        if user and len(user) > 0:
            user = user[0]
        # if user:
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

##########

##########

@app.route('/api/register', methods=['POST'])
def api_register():
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        membership_number = data.get('membership_number', '').strip()
        role = data.get('role', '').strip()
        
        if not name or not email or not password:
            return jsonify({"success": False, "error": "Name, email, and password are required"}), 400
        
        if len(password) < 6:
            return jsonify({"success": False, "error": "Password must be at least 6 characters"}), 400
        
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Check for duplicates
        email_check = b.universal_db_select("SELECT id FROM users WHERE email = %s", (email,))
        if email_check and len(email_check) > 0:
            return jsonify({"success": False, "error": "Email already exists"}), 409
        
        if membership_number:
            member_check = b.universal_db_select("SELECT id FROM users WHERE membership_number = %s", (membership_number,))
            if member_check and len(member_check) > 0:
                return jsonify({"success": False, "error": "Membership number already exists"}), 409
        
        # Insert user (works for both databases)
        insert_query = """
            INSERT INTO users (name, email, password, membership_number, role)
            VALUES (%s, %s, %s, %s, %s)
        """
        # -- VALUES (%s, %s, %s, %s, 'member')

        insert_result = b.db_insert(insert_query, (name, email, hashed_password, membership_number or None, role))
        
        # Check if insert was successful
        if insert_result is None or insert_result <= 0:
            return jsonify({"success": False, "error": "Registration failed - duplicate entry or database error"}), 409
        
        # Get the newly created user by email (most reliable method)
        new_user = b.universal_db_select(
            "SELECT id, name, email, role, membership_number FROM users WHERE email = %s", 
            (email,)
        )
        
        if not new_user or len(new_user) == 0:
            # If query by email fails, try a broader search
            new_user = b.universal_db_select(
                "SELECT id, name, email, role, membership_number FROM users WHERE email = %s OR name = %s ORDER BY id DESC LIMIT 1", 
                (email, name)
            )
            
        if not new_user or len(new_user) == 0:
            return jsonify({"success": False, "error": "User created but could not be retrieved from database"}), 500
        
        user_data = new_user[0]
        
        from datetime import datetime, timezone, timedelta
        
        token = jwt.encode({
            'user_id': user_data['id'],
            'email': user_data['email'],
            'role': user_data['role'],
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)
        }, os.getenv('JWT_SECRET', 'fallback-secret'), algorithm='HS256')
        
        return jsonify({
            "success": True,
            "message": "Registration successful",
            "user": user_data,
            "token": token
        })
            
    except Exception as e:
        error_msg = str(e).lower()
        if "duplicate" in error_msg or "unique" in error_msg:
            return jsonify({"success": False, "error": "Email or membership number already exists"}), 409
        return jsonify({"success": False, "error": f"Registration failed: {str(e)}"}), 500
    

def get_books_with_search(search_term, limit, offset):
    """Universal search that works with both MySQL and PostgreSQL"""
    
    if b.DB_TYPE == 'mysql':
        query = """
            SELECT 
                b.id as book_id,
                b.title as book_title,
                b.author,
                b.category_id,
                cat.name as category_name,
                c.id as chapter_id,
                c.chapter_number,
                c.title as chapter_title
            FROM books b
            LEFT JOIN categories cat ON b.category_id = cat.id
            LEFT JOIN chapters c ON b.id = c.book_id 
            WHERE MATCH(b.title) AGAINST (%s IN BOOLEAN MODE)
               OR MATCH(b.author) AGAINST (%s IN BOOLEAN MODE)
               OR MATCH(cat.name) AGAINST (%s IN BOOLEAN MODE)
            ORDER BY b.title, c.chapter_number
            LIMIT %s OFFSET %s
        """
        # Use the search term as-is (full-text handles it)
        params = (search_term, search_term, search_term, limit, offset)
        
    elif b.DB_TYPE == 'postgresql':
        # PostgreSQL with citext (simple LIKE is now case-insensitive)
        query = """
            SELECT 
                b.id as book_id,
                b.title as book_title,
                b.author,
                b.category_id,
                cat.name as category_name,
                c.id as chapter_id,
                c.chapter_number,
                c.title as chapter_title
            FROM books b
            LEFT JOIN categories cat ON b.category_id = cat.id
            LEFT JOIN chapters c ON b.id = c.book_id 
            WHERE b.title LIKE %s OR b.author LIKE %s OR cat.name LIKE %s
            ORDER BY b.title, c.chapter_number
            LIMIT %s OFFSET %s
        """
        # Use pattern matching for LIKE
        search_pattern = f'%{search_term}%'
        params = (search_pattern, search_pattern, search_pattern, limit, offset)
        # print("get_books_with_search() 1111")
    else: 
        # Fallback for other databases
        print("Fallback for other databases")
        query = """
            SELECT 
                b.id as book_id,
                b.title as book_title,
                b.author,
                b.category_id,
                cat.name as category_name,
                c.id as chapter_id,
                c.chapter_number,
                c.title as chapter_title
            FROM books b
            LEFT JOIN categories cat ON b.category_id = cat.id
            LEFT JOIN chapters c ON b.id = c.book_id 
            WHERE b.title LIKE %s OR b.author LIKE %s OR cat.name LIKE %s
            ORDER BY b.title, c.chapter_number
            LIMIT %s OFFSET %s
        """
        search_pattern = f'%{search_term}%'
        params = (search_pattern, search_pattern, search_pattern, limit, offset)
    
    return b.universal_db_select(query, params)

@app.route('/books', methods=['GET'])
def get_books():
    try:
        # print("get_books()")
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        search = request.args.get('search', '', type=str)
        offset = (page - 1) * limit

        # Build query based on search
        if search:
            # Use the universal search function
            
            results = get_books_with_search(search, limit, offset)
            # print(results)

            # Get total count for search
            if b.DB_TYPE == 'mysql':
                count_query = """
                    SELECT COUNT(DISTINCT b.id) as total
                    FROM books b
                    LEFT JOIN categories cat ON b.category_id = cat.id
                    WHERE MATCH(b.title) AGAINST (%s)
                       OR MATCH(b.author) AGAINST (%s)
                       OR MATCH(cat.name) AGAINST (%s)
                """
                total_count = b.universal_db_select(count_query, (search, search, search))
            else: # postgesql
                count_query = """
                    SELECT COUNT(DISTINCT b.id) as total
                    FROM books b
                    LEFT JOIN categories cat ON b.category_id = cat.id
                    WHERE b.title LIKE %s OR b.author LIKE %s OR cat.name LIKE %s
                """
                search_pattern = f'%{search}%'
                total_count = b.universal_db_select(count_query, (search_pattern, search_pattern, search_pattern))
        
        else:
            query = """
                SELECT 
                    b.id as book_id,
                    b.title as book_title,
                    b.author,
                    b.category_id,
                    cat.name as category_name,
                    c.id as chapter_id,
                    c.chapter_number,
                    c.title as chapter_title
                FROM books b
                LEFT JOIN categories cat ON b.category_id = cat.id
                LEFT JOIN chapters c ON b.id = c.book_id 
                ORDER BY b.title, c.chapter_number
                LIMIT %s OFFSET %s
            """
            results = b.universal_db_select(query, (limit, offset))


            # books_results = b.universal_db_select(books_query, (limit, offset))
            # books_with_chapters_results = b.universal_db_select(books_with_chapters_query, (limit, offset))

            total_count = b.universal_db_select("SELECT COUNT(*) as total FROM books")

        # Process results (same as before)
        if results is None:
            results = []

        # if results is None:
        #     return jsonify({
        #         "success": True,
        #         "books": [],
        #         "pagination": {
        #             "page": page,
        #             "limit": limit,
        #             "total": 0,
        #             "pages": 0
        #         }
        #     })
        
        # Process results
        books = {}
        for row in results:
            book_id = row['book_id']
            if book_id not in books:
                books[book_id] = {
                    'id': book_id,
                    'title': row['book_title'],
                    'author': row.get('author', ''),
                    'category_id': row.get('category_id'),
                    'category_name': row.get('category_name', ''),
                    'chapters': []
                }
            
            if row.get('chapter_id'):
                books[book_id]['chapters'].append({
                    'id': row['chapter_id'],
                    'chapter_number': row['chapter_number'],
                    'title': row['chapter_title']
                })
        
        books_list = list(books.values())
        total = total_count[0]['total'] if total_count and len(total_count) > 0 else 0
        
        response = jsonify({
            "success": True,
            "books": books_list,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": math.ceil(total / limit) if total > 0 else 0
            }
        })
        response.headers["Cache-Control"] = "public, max-age=300"
        return response

    except Exception as e:
        print(f"Error fetching books: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500
        


def generate_signed_url(bucket_name, file_path, expiration=3600):
    """Generate a signed URL for private Backblaze B2 files"""
    try:
        # s3 = s.backblaze_store()
        s3 = bz
        
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

##########
def record_audio_play(user_id, book_id, chapter_id=None, duration=0, progress=0):
# def record_audio_play(user_id, book_id, chapter_id=None, current_chapter=None, progress=0):
    """
    Record audio play in access_history - but only if no recent record exists
    Returns True if a new record was created, False if an existing record was updated
    """
    try:
        # First, check if there's a recent record for this user/book/chapter combination
        # (within the last 5 minutes) that we should update instead of creating a new one
        if chapter_id:
            check_query = """
                SELECT id, duration, progress 
                FROM access_history 
                WHERE user_id = %s 
                AND book_id = %s 
                AND chapter_id = %s 
                AND accessed_at >= NOW() - INTERVAL '5 minutes'
                ORDER BY accessed_at DESC 
                LIMIT 1
            """
            params = (user_id, book_id, chapter_id)
        else:
            check_query = """
                SELECT id, duration, progress 
                FROM access_history 
                WHERE user_id = %s 
                AND book_id = %s 
                AND chapter_id IS NULL 
                AND accessed_at >= NOW() - INTERVAL '5 minutes'
                ORDER BY accessed_at DESC 
                LIMIT 1
            """
            params = (user_id, book_id)
        
        existing_record = b.db_select(check_query, params, fetch_one=True)
        
        if existing_record:
            # Update the existing record instead of creating a new one
            record_id, current_duration, current_progress = existing_record
            
            # Only update if the new progress is greater than current progress
            if progress > current_progress:
                update_query = """
                    UPDATE access_history 
                    SET progress = %s, 
                        duration = GREATEST(duration, %s),
                        accessed_at = NOW()
                    WHERE id = %s
                """
                b.db_update(update_query, (progress, progress, record_id))
                print(f"✅ Updated existing record {record_id} with progress {progress}")
                return False  # Indicate that we updated, not created
            else:
                print(f"ℹ️ Keeping existing record {record_id} (progress {current_progress} >= new {progress})")
                return False
        
        # If no recent record exists, create a new one
        query = """
            INSERT INTO access_history 
            (user_id, book_id, chapter_id, progress, duration, accessed_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """
        params = (user_id, book_id, chapter_id, duration, progress)
        
        b.db_insert(query, params)
        print(f"✅ Created new record for user {user_id}, book {book_id}, chapter {chapter_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error recording audio play: {e}")
        return False

    
@app.route('/api/record-play', methods=['POST'])
def api_record_play():
    """API endpoint to record audio plays"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        book_id = data.get('book_id')
        chapter_id = data.get('chapter_id')
        duration = data.get('duration', 0)
        progress = data.get('progress', 0)
        
        if not user_id or not book_id:
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        success = record_audio_play(user_id, book_id, chapter_id, duration, progress)
        
        return jsonify({"success": success})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
##########



def remove_from_favorites(user_id, book_id):
    """Remove a book from user's favorites"""
    try:
        query = "DELETE FROM favorites WHERE user_id = %s AND book_id = %s"
        result = b.db_execute(query, (user_id, book_id))
        return result is not None
        
    except Exception as e:
        print(f"❌ Error removing from favorites: {str(e)}")
        return False

def is_book_favorite(user_id, book_id):
    """Check if a book is in user's favorites"""
    try:
        query = "SELECT id FROM favorites WHERE user_id = %s AND book_id = %s"
        result = b.universal_db_select(query, (user_id, book_id))
        return len(result) > 0
    except:
        return False

########
def get_chapter_by_number(book_id, chapter_number):
    """Get chapter by chapter number"""
    try:
        result = b.universal_db_select(
            "SELECT * FROM chapters WHERE book_id = %s AND chapter_number = %s",
            (book_id, chapter_number)
        )
        return result[0] if result else None
    except:
        return None    

@app.route('/api/chapter/by-number', methods=['GET'])
def api_get_chapter_by_number():
    """API endpoint to get chapter by number"""
    try:
        book_id = request.args.get('book_id', type=int)
        chapter_number = request.args.get('chapter_number', type=int)
        
        if not book_id or not chapter_number:
            return jsonify({"success": False, "error": "book_id and chapter_number are required"}), 400
        
        chapter = get_chapter_by_number(book_id, chapter_number)
        
        if chapter:
            return jsonify({"success": True, "chapter": chapter})
        else:
            return jsonify({"success": False, "error": "Chapter not found"}), 404
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
########

########
@app.route('/api/chapters', methods=['GET'])
def api_get_chapters():
    """API endpoint for various chapter operations"""
    try:
        print("api_get_chapters()")
        # Get by ID
        chapter_id = request.args.get('id', type=int)
        print(f"api_get_chapters : 1 {chapter_id}")
        if chapter_id:
            print("api_get_chapters : 1.5")
            chapter = get_chapter_by_id(chapter_id)
            if chapter:
                print("api_get_chapters : 2")
                return jsonify({"success": True, "chapter": chapter})
            else:
                print("api_get_chapters : 3")
                return jsonify({"success": False, "error": "Chapter not found"}), 404
        
        # Get by book ID and chapter number
        book_id = request.args.get('book_id', type=int)
        chapter_number = request.args.get('chapter_number', type=int)
        
        if book_id and chapter_number:
            chapter = get_chapter_by_number(book_id, chapter_number)
            if chapter:
                print("api_get_chapters : 4")
                return jsonify({"success": True, "chapter": chapter})
            else:
                print("api_get_chapters : 5")
                return jsonify({"success": False, "error": "Chapter not found"}), 404
        
        # Get all chapters for a book
        print("api_get_chapters : 6")
        if book_id:
            print(f"api_get_chapters : 7  {book_id}")
            chapters = get_book_chapters(book_id)
            # chapters = get_book_chapters(book_id)
            # print(f"api_get_chapters : 8 {chapters}")
            return jsonify({"success": True, "chapters": chapters})     #"Non chapters"
        
        return jsonify({"success": False, "error": "Invalid parameters"}), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def get_chapter_by_id(chapter_id):
    """Get chapter by ID"""
    try:
        result = b.universal_db_select("SELECT * FROM chapters WHERE id = %s", (chapter_id,))
        return result[0] if result else None
    except:
        return None
    
def get_book_chapters(book_id):
    query = "SELECT title, chapter_number FROM chapters WHERE book_id = %s ORDER BY chapter_number"
    return b.universal_db_select(query, (book_id,))

########

######## my_library - show_recently_played - show_recently_played ########
# Database helper functions (to be implemented)
def get_recently_played(user_id, limit=10):
    """Get user's recently played books from database with detailed progress"""
    try:
        query = """
            SELECT DISTINCT ON (b.id, ah.chapter_id)
                b.id, 
                b.title, 
                b.author, 
                ah.accessed_at as last_played,
                ah.progress, 
                ah.duration,
                ah.chapter_id, 
                c.title as current_chapter,
                c.chapter_number
            FROM access_history ah
            JOIN books b ON ah.book_id = b.id
            LEFT JOIN chapters c ON ah.chapter_id = c.id
            WHERE ah.user_id = %s
            ORDER BY b.id, ah.chapter_id, ah.accessed_at DESC
            LIMIT %s
        """
        results = b.universal_db_select(query, (user_id, limit))
        
        # Debug: Print what we're getting from the database
        # print(f"📊 Raw database results for user {user_id}:")
        # for i, book in enumerate(results):
        #     print(f"  Book {i+1}: ID={book['id']}, Progress={book.get('progress', 'N/A')}, Duration={book.get('duration', 'N/A')}")
        
        return results
        # results = b.universal_db_select(query, (user_id, limit))
        # return results
    except Exception as e:
        print(f"❌ Error getting recently played: {str(e)}")
        return []
    
    
@app.route('/api/get_recently-played', methods=['GET'])
def api_get_recently_played():
    """API endpoint to get user's recently played books"""
    # print("api_get_recently_played()")
    try:
        user_id = request.args.get('user_id')
        limit = request.args.get('limit', 10, type=int)

        if not user_id:
            return jsonify({"success": False, "error": "User ID is required"}), 400
        
        # Validate limit
        if limit > 50:  # Prevent excessive queries
            limit = 50
        elif limit < 1:
            limit = 10
        
        recently_played = get_recently_played(user_id, limit)
        
        return jsonify({
            "success": True,
            "data": recently_played,
            "count": len(recently_played),
            "user_id": user_id
        })
        
    except Exception as e:
        print(f"❌ Error in /api/recently-played: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch recently played books",
            "message": str(e)
        }), 500
######## my_library - show_recently_played - show_recently_played ########

######## my_library - get_book_by_id ########
def get_book_by_id(book_id):
    try:
        result = b.universal_db_select("""
            SELECT b.*, c.name as category_name 
            FROM books b 
            LEFT JOIN categories c ON b.category_id = c.id 
            WHERE b.id = %s
        """, (book_id,))
        return result[0] if result else None
    except Exception as e:
        print(f"❌ Error getting book by ID: {str(e)}")
        return None
    
@app.route('/api/books/<int:book_id>', methods=['GET'])
def api_get_book_by_id(book_id):
    """API endpoint to get book by ID"""
    try:
        book = get_book_by_id(book_id)
        
        if book:
            return jsonify({
                "success": True,
                "book": book
            })
        else:
            return jsonify({
                "success": False,
                "error": "Book not found"
            }), 404
            
    except Exception as e:
        print(f"❌ Error in /api/books/{book_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to fetch book",
            "message": str(e)
        }), 500

######## my_library - record_download ########
def record_download(user_id, book_id, chapter_id, file_path, file_size):
    """Record a download in the database"""
    try:
        query = """
            INSERT INTO downloads (user_id, book_id, chapter_id, file_path, file_size)
            VALUES (%s, %s, %s, %s, %s)
        """
        result = b.db_execute(query, (user_id, book_id, chapter_id, file_path, file_size))
        return result is not None
    except Exception as e:
        print(f"❌ Error recording download: {str(e)}")
        return False

@app.route('/api/record-download', methods=['POST'])
def api_record_download():
    """API endpoint to record a download"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        book_id = data.get('book_id')
        chapter_id = data.get('chapter_id')
        file_path = data.get('file_path')
        file_size = data.get('file_size')
        
        # Validate required fields
        if not all([user_id, book_id, file_path, file_size]):
            return jsonify({
                "success": False, 
                "error": "Missing required fields: user_id, book_id, file_path, file_size"
            }), 400
        
        # Use your existing function
        success = record_download(user_id, book_id, chapter_id, file_path, file_size)
        
        return jsonify({
            "success": success,
            "message": "Download recorded successfully" if success else "Failed to record download"
        })
        
    except Exception as e:
        print(f"❌ Error in /api/record-download: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to record download",
            "message": str(e)
        }), 500
######## my_library - record_download ########

######## my_library - update_playback_progress/playback ########
######## browse_books - update_playback_progress/playback ########
def update_playback(user_id, book_id, chapter_id=None, duration=0, progress=0):
    """Update playback progress in database"""
    print("update_playback()")
    try:
        # print(f"🗄️ Starting DB update for user {user_id}, book {book_id}")
        
        # Ensure integers
        duration = int(round(duration))
        progress = int(round(progress))
        
        # print(f"🔢 Final values - duration: {duration} (type: {type(duration)}), progress: {progress} (type: {type(progress)})")

        if DB_TYPE == "postgresql":
            query = """
                WITH cte AS (
                    SELECT id
                    FROM access_history
                    WHERE user_id = %s
                      AND book_id = %s
                      AND (chapter_id = %s OR (%s IS NULL AND chapter_id IS NULL))
                    ORDER BY accessed_at DESC
                    LIMIT 1
                )
                UPDATE access_history ah
                SET duration = %s,
                    progress = %s,
                    accessed_at = NOW()
                FROM cte
                WHERE ah.id = cte.id
            """
            params = (user_id, book_id, chapter_id, chapter_id, duration, progress)

        else:  # MySQL supports ORDER BY + LIMIT
            query = """
                UPDATE access_history 
                SET duration = %s, progress = %s, accessed_at = NOW()
                WHERE user_id = %s AND book_id = %s 
                  AND (chapter_id = %s OR (%s IS NULL AND chapter_id IS NULL))
                ORDER BY accessed_at DESC
                LIMIT 1
            """
            params = (duration, progress, user_id, book_id, chapter_id, chapter_id)

        # print(f"📝 Executing query: {query}")
        # print(f"duration = {duration}, progress = {progress}, user_id = {user_id}, book_id = {book_id}, chapter_id = {chapter_id}, chapter_id = {chapter_id}")
        result = b.db_update(query, params)
        # print(f"✅ DB update result: {result}")
        
        # Check if any rows were affected
        if hasattr(result, 'rowcount'):
            print(f"📊 Rows affected: {result.rowcount}")

        return result is not None

    except Exception as e:
        print(f"❌ Error updating playback in DB: {str(e)}")
        return False


@app.route('/api/update-playback', methods=['POST'])
def api_update_playback():
    """API endpoint to update playback progress"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        book_id = data.get('book_id')
        chapter_id = data.get('chapter_id')
        duration = data.get('duration', 0)
        progress = data.get('progress', 0)
        
        if not all([user_id, book_id]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        success = update_playback(user_id, book_id, chapter_id, duration, progress)
        
        return jsonify({
            "success": success,
            "message": "Progress updated successfully" if success else "Failed to update progress"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

######## my_library - update_playback_progress/playback ########
######## browse_books - update_playback_progress/playback ########



import requests

if __name__ == "__main__":
    # print("Testing database connection...")
    b.check_database_status()
    # s.check_backblaze_status()
    # app.run(debug=True, port=8000)
    app.run(debug=True, host="0.0.0.0", port=8000)
else:
    # Vercel serverless function handler
    def handler(event, context):
        with app.app_context():
            # This will be handled by Vercel's Python runtime
            return app(event, context)