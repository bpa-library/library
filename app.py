from flask import Flask, jsonify
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

@app.route('/debug')
def debug():
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


# def get_db():
#     try:
#         return mysql.connector.connect(
#             host=b.DB_HOST,
#             user=b.DB_USER,
#             password=b.DB_PASSWORD,
#             database=b.DB_NAME,
#             port=int(b.DB_PORT)
#         )
#     except Exception as e:
#         print(f"DB Error: {str(e)}")
#         return None
    

# def get_db():
#     try:
#         db_user = os.getenv('DB_USER', 'root')
#         db_pass = os.getenv('DB_PASSWORD', 'xpbwmzchXSacGsreDkLWIpecGCeVqymd')
#         db_name = os.getenv('DB_NAME', 'railway')
#         db_host = os.getenv('DB_HOST', 'shuttle.proxy.rlwy.net')
#         db_port = int(os.getenv('DB_PORT', '46029'))
#         # db_host = os.getenv('DB_HOST', 'mysql.railway.internal')
#         # db_port = int(os.getenv('DB_PORT', '3306'))

#         print(f"Attempting connection to: {db_user}@{db_host}:{db_port}/{db_name}")

#         return mysql.connector.connect(
#             host=db_host,
#             user=db_user,
#             password=db_pass,
#             database=db_name,
#             port=db_port
#         )

#     except ValueError as ve:
#         print(f"Port conversion error: {str(ve)}")
#         return None
#     except mysql.connector.Error as err:
#         print(f"MySQL Connection Error: {err}")
#         return None
#     except Exception as e:
#         print(f"General connection error: {str(e)}")
#         return None

    

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
        return jsonify({"books": books})
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
    


