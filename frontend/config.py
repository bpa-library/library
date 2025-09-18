# config.py
###########
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_URL = os.getenv('API_URL')
#API_URL = os.getenv('API_URL', 'http://localhost:8000')
#DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///library.db')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
# SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Better error handling
if not API_URL:
    print("⚠️  API_URL not found in .env file, using default localhost")
    API_URL = "http://localhost:8000"

print(f"✅ API_URL: {API_URL}")



