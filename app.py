
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
import math  # Add this import at the top of your file
from datetime import datetime, timezone, timedelta  #

# from dotenv import load_dotenv

#from serverless_wsgi import handle_request

# load_dotenv()  # Load .env file for local development

# def handler(event, context):
#     return handle_request(app, event, context)

DB_TYPE = os.getenv('DB_TYPE').lower()   # MySQL / postgreSQL
# db = 'MySQL'
# db = 'postgreSQL'

# PostgreSQL - Free Forever - https://neon.com/ - (Neon.tech)
# Free Limit 3GB storage, Beyond Free $0.10/GB
# from sqlalchemy import create_engine, text
# import psycopg2


app = Flask(__name__)
CORS(app) 


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
    
@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    email = data.get('email')  # Using email instead of username
    password = data.get('password')
    
    # Hash password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    # Check credentials with role validation
    user = b.universal_db_select(
        "SELECT id, name, email, role FROM users WHERE email = %s AND password = %s AND role = 'admin'",
        (email, hashed_password)
    )
    
    if user and len(user) > 0:
        user_data = user[0]
        token = jwt.encode({
            'user_id': user_data['id'],
            'email': user_data['email'],
            'role': user_data['role'],
            'exp': datetime.now(timezone.utc) + timedelta(hours=8)
        }, os.getenv('JWT_SECRET'), algorithm='HS256')
        
        return jsonify({
            "success": True,
            "token": token,
            "user": {
                "id": user_data['id'],
                "name": user_data['name'],
                "email": user_data['email'],
                "role": user_data['role']
            }
        })
    
    return jsonify({"success": False, "error": "Invalid admin credentials"}), 401

@app.route('/admin/books', methods=['POST'])
@admin_required
def add_book():
    try:
        data = request.get_json()
        query = """
            INSERT INTO books (title, author, publisher, isbn, description, category_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        result = b.db_insert(query, (
            data['title'], data['author'], data['publisher'], 
            data['isbn'], data['description'], data['category_id']
        ))
        
        return jsonify({"book_id": result, "message": "Book added successfully"}), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/upload-audio', methods=['POST'])
@admin_required
def upload_audio():
    try:
        book_id = request.form.get('book_id')
        file = request.files.get('audio_file')
        
        if not file:
            return jsonify({"error": "No file provided"}), 400
        
        # Get book info for folder structure
        book = b.universal_db_select("SELECT title, author FROM books WHERE id = %s", (book_id,))
        if not book:
            return jsonify({"error": "Book not found"}), 404
        
        # Create folder path: "Title By Author"
        folder_name = f"{book[0]['title']} By {book[0]['author']}"
        file_path = f"{folder_name}/{file.filename}"
        
        # Upload to Backblaze
        s3 = s.backblaze_store()
        s3.upload_fileobj(file, os.getenv('B2_BUCKET'), file_path)
        
        # Add chapter to database
        chapter_query = "INSERT INTO chapters (book_id, title) VALUES (%s, %s)"
        b.db_insert(chapter_query, (book_id, file.filename))
        
        return jsonify({"message": "Audio uploaded successfully", "path": file_path})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
###################
@app.route('/admin/users', methods=['GET'])
@admin_required
def get_users():
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        offset = (page - 1) * limit
        
        users = b.universal_db_select(
            "SELECT id, name, email, role, membership_number FROM users ORDER BY id LIMIT %s OFFSET %s",
            (limit, offset)
        )
        
        total_count = b.universal_db_select("SELECT COUNT(*) as total FROM users")
        total = total_count[0]['total'] if total_count else 0
        
        return jsonify({
            "success": True,
            "users": users,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": math.ceil(total / limit) if total > 0 else 0
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/users/<int:user_id>/role', methods=['PUT'])
@admin_required
def update_user_role(user_id):
    try:
        data = request.get_json()
        new_role = data.get('role')
        
        if new_role not in ['member', 'admin']:
            return jsonify({"success": False, "error": "Invalid role"}), 400
        
        result = b.db_execute(
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


###################

###################

# Add this endpoint to your Flask app
@app.route('/api/audio-url/<int:book_id>/<path:chapter_title>')
def get_audio_url(book_id, chapter_title):
    try:
        # The chapter_title is now automatically URL decoded by Flask
        # No need to urllib.parse.unquote() it
    
        # Get book title from database
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


# # Add this endpoint to your Flask app
# @app.route('/api/audio-url/<int:book_id>/<path:chapter_title>')
# def get_audio_url(book_id, chapter_title):
    try:
        # The chapter_title is now automatically URL decoded by Flask
        # No need to urllib.parse.unquote() it
    
        # Get book title from database
        book_result = b.universal_db_select("SELECT title FROM books WHERE id = %s", (book_id,))

        if not book_result or len(book_result) == 0:
            return jsonify({"error": "Book not found"}), 404
        
        book = book_result[0]

        # Generate file path
        # file_path = f"{book['title']}/{chapter_title}"

        import urllib.parse
        decoded_title = urllib.parse.unquote(chapter_title)
        file_path = f"{book['title']}/{decoded_title}"
        # Generate signed URL
        #file_path = f"{book['title']}/{chapter_title}"
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
    return jsonify({"status": "healthy", "db": "ok" if MySQL_db() else "down"})
    
@app.route('/debug')
def debug():
    X_AUTH_SECRET = os.getenv('X_AUTH_SECRET')
    if not X_AUTH_SECRET:
        raise ValueError("Missing X_AUTH_SECRET in .env file")
    
    if not request.headers.get('X-Auth') == os.getenv('X_AUTH_SECRET'):
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({
        "db_status": "Connected" if MySQL_db() else "Failed",
        "env_vars": {k:v for k,v in os.environ.items() if k.startswith('DB_')}
    })

# def backblaze_store():
#     return boto3.client(
#         's3',
#         endpoint_url='https://s3.eu-central-003.backblazeb2.com',  # Use your actual endpoint
#         aws_access_key_id=os.getenv('B2_KEY_ID'),
#         aws_secret_access_key=os.getenv('B2_APP_KEY')
#     )

# def backblaze_store():
#     try:
#         return boto3.client(
#             's3',
#             endpoint_url=os.getenv('B2_ENDPOINT'),
#             aws_access_key_id=os.getenv('B2_KEY_ID'),
#             aws_secret_access_key=os.getenv('B2_APP_KEY'),
#             region_name=os.getenv('region_name')
#         )
#     except Exception as e:
#         print(f"❌ Backblaze B2 connection failed: {str(e)}")
#         return False

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
            VALUES (%s, %s, %s, %s, 'member')
        """
        
        insert_result = b.db_insert(insert_query, (name, email, hashed_password, membership_number or None))
        
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
    
    else:
        # Fallback for other databases
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
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 50, type=int)
        search = request.args.get('search', '', type=str)
        offset = (page - 1) * limit

        # Build query based on search
        if search:
            # Use the universal search function
            results = get_books_with_search(search, limit, offset)

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
            else:
                count_query = """
                    SELECT COUNT(DISTINCT b.id) as total
                    FROM books b
                    LEFT JOIN categories cat ON b.category_id = cat.id
                    WHERE b.title LIKE %s OR b.author LIKE %s OR cat.name LIKE %s
                """
                search_pattern = f'%{search}%'
                total_count = b.universal_db_select(count_query, (search_pattern, search_pattern, search_pattern))
        
        else:
            # No search - simple pagination
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
        
# @app.route('/books', methods=['GET'])
# def get_books():
#     try:
#         # Use parameterized query with optional parameters
#         page = request.args.get('page', 1, type=int)
#         limit = request.args.get('limit', 50, type=int)
#         offset = (page - 1) * limit

#         query = """
#             SELECT 
#                 b.id as book_id,
#                 b.title as book_title,
#                 b.author,
#                 b.category_id,  -- Changed from b.category
#                 c.id as chapter_id,
#                 c.chapter_number,
#                 c.title as chapter_title
#             FROM books b
#             LEFT JOIN chapters c ON b.id = c.book_id 
#             ORDER BY b.title, c.chapter_number
#             LIMIT %s OFFSET %s
#         """

#         results = b.universal_db_select(query, (limit, offset))
        
#         if results is None:  # Handle case where function returns None
#             return jsonify({"books": [], "message": "No books found"})
        
#         books = {}
#         for row in results:
#             book_id = row['book_id']
#             if book_id not in books:
#                 books[book_id] = {
#                     'id': book_id,
#                     'title': row['book_title'],
#                     'author': row.get('author', ''),
#                     'category_id': row.get('category_id'),  # Changed from category
#                     'chapters': []
#                 }
            
#             # Add chapter if it exists
#             if row.get('chapter_id'):
#                 books[book_id]['chapters'].append({
#                     'id': row['chapter_id'],
#                     'chapter_number': row['chapter_number'],
#                     'title': row['chapter_title']
#                 })
        
#         books_list = list(books.values())
        
#         response = jsonify({
#             "success": True,
#             "books": books_list,
#             "pagination": {
#                 "page": page,
#                 "limit": limit,
#                 "count": len(books_list)
#             }
#         })
#         response.headers["Cache-Control"] = "public, max-age=3600"
#         return response

#     except Exception as e:
#         print(f"Error fetching books: {str(e)}")
#         return jsonify({
#             "success": False,
#             "error": "Internal server error",
#             "message": str(e)
#         }), 500
    

# @app.route('/books', methods=['GET'])
# def get_books():
#     try:
#         db = MySQL_db()
#         if db is None:
#             return jsonify({"error": "Database connection failed"}), 500
#             # return jsonify({"error": "DB connection failed", "env": dict(os.environ)}), 500
        
#         cursor = db.cursor(dictionary=True)
#         cursor.execute("""
#                     SELECT 
#                         b.id as book_id,
#                         b.title as book_title,
#                         c.id as chapter_id,
#                         c.chapter_number,
#                         c.title as chapter_title
#                     FROM books b
#                     INNER JOIN chapters c ON b.id = c.book_id 
#                     ORDER BY b.title, c.chapter_number
#                     LIMIT 10
#                 """)
#         results = cursor.fetchall()

#         books = {}
#         for row in results:
#             book_id = row['book_id']
#             if book_id not in books:
#                 books[book_id] = {
#                     'id': book_id,
#                     'title': row['book_title'],
#                     'chapters': []
#                 }
            
#             if row['chapter_id']:  # Only add if chapter exists
#                 books[book_id]['chapters'].append({
#                     'title': row['chapter_title'],
#                     'id': row['chapter_id'],
#                     'chapter_number': row['chapter_number']
#                 })
        
#         return jsonify({"books": list(books.values())})

#         # response = jsonify({"books": books})
#         # response.headers["Cache-Control"] = "public, max-age=3600"  # 1 hour cache
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
#     finally:
#         if 'cursor' in locals(): cursor.close()
#         if 'db' in locals(): db.close()

# Storage - Backblaze connection
# def upload_to_b2(file_path):
    s3 = boto3.client(
        's3',
        endpoint_url=os.getenv('B2_ENDPOINT'),
        aws_access_key_id=os.getenv('B2_KEY_ID'),
        aws_secret_access_key=os.getenv('B2_APP_KEY')
    )
    
    try:
        file_name = os.path.basename(file_path)
        B2_BUCKET = os.getenv('B2_BUCKET')
        s3.upload_file(file_path, B2_BUCKET, file_name)
        print(f"Successfully uploaded {file_name} to {B2_BUCKET}")
        return True
    except Exception as e:
        print(f"Upload failed: {str(e)}")
        return False

    # Test upload
    file_path = r"E:\Books-Audible\The Girl in Room 105 (Hindi)\Chapter 05.mp3"
    
    # Verify file exists first
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
    else:
        if upload_to_b2(file_path):
            print("Starting Flask server...")
            app.run(host="0.0.0.0", port=8000)

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


def generate_signed_url(bucket_name, file_path, expiration=3600):
    """Generate a signed URL for private Backblaze B2 files"""
    try:
        s3 = s.backblaze_store()
        
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
    """Record when a user plays an audio file"""
    try:
        if not user_id:
            print("⚠️ Cannot record play: No user ID")
            return False
        
        query = """
            INSERT INTO access_history (user_id, book_id, chapter_id, duration, progress)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING  -- For PostgreSQL, or use INSERT IGNORE for MySQL
        """
        
        # For MySQL, use this query instead:
        if DB_TYPE == 'mysql':
            query = """
                INSERT IGNORE INTO access_history (user_id, book_id, chapter_id, duration, progress)
                VALUES (%s, %s, %s, %s, %s)
            """
        
        result = b.db_execute(query, (user_id, book_id, chapter_id, duration, progress))
        return result is not None
        
    except Exception as e:
        print(f"❌ Error recording audio play: {str(e)}")
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
        
        # Use your existing record function
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
        # Get by ID
        chapter_id = request.args.get('id', type=int)
        if chapter_id:
            chapter = get_chapter_by_id(chapter_id)
            if chapter:
                return jsonify({"success": True, "chapter": chapter})
            else:
                return jsonify({"success": False, "error": "Chapter not found"}), 404
        
        # Get by book ID and chapter number
        book_id = request.args.get('book_id', type=int)
        chapter_number = request.args.get('chapter_number', type=int)
        
        if book_id and chapter_number:
            chapter = get_chapter_by_number(book_id, chapter_number)
            if chapter:
                return jsonify({"success": True, "chapter": chapter})
            else:
                return jsonify({"success": False, "error": "Chapter not found"}), 404
        
        # Get all chapters for a book
        if book_id:
            chapters = get_book_chapters(book_id)
            return jsonify({"success": True, "chapters": chapters})
        
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
########



# if __name__ == "__main__":
#     print("Testing database connection...")
    
    # test_db = MySQL_db()
    # if test_db:
    #     print("✅ Connected to Railway Database successful!")
    #     test_db.close()
    # else:
    #     print("❌ Railway Database connection failed - check credentials")

    # catagry()

    # test_b2_connection()
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

    # app.run(host="0.0.0.0", port=8000)

import requests

if __name__ == "__main__":
    print("Testing database connection...")
    app.run(debug=True, port=8000)
    # app.run(debug=True, host="0.0.0.0", port=8000)
else:
    # Vercel serverless function handler
    def handler(event, context):
        with app.app_context():
            # This will be handled by Vercel's Python runtime
            return app(event, context)