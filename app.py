import streamlit as st
import mysql.connector
import hashlib
import re
from datetime import datetime, timedelta
import jwt
import os

# Database connection function
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=st.secrets["DB_HOST"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            database=st.secrets["DB_NAME"],
            port=st.secrets["DB_PORT"]
        )
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        return None

# Password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# JWT token generation
def generate_token(user_id, email, role):
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, st.secrets["JWT_SECRET"], algorithm='HS256')

# Validate email format
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Login function
def login_user(email, password):
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(dictionary=True)
        hashed_password = hash_password(password)
        
        cursor.execute("""
            SELECT id, name, email, role, membership_number 
            FROM users 
            WHERE email = %s AND password = %s
        """, (email, hashed_password))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            token = generate_token(user['id'], user['email'], user['role'])
            return {**user, 'token': token}
        return None
        
    except Exception as e:
        st.error(f"Login error: {str(e)}")
        return None

# Registration function
def register_user(name, email, password, membership_number=None):
    if not is_valid_email(email):
        return "Invalid email format"
    
    conn = get_db_connection()
    if not conn:
        return "Database connection failed"
    
    try:
        cursor = conn.cursor()
        hashed_password = hash_password(password)
        
        cursor.execute("""
            INSERT INTO users (name, email, password, membership_number)
            VALUES (%s, %s, %s, %s)
        """, (name, email, hashed_password, membership_number))
        
        conn.commit()
        cursor.close()
        conn.close()
        return "Registration successful!"
        
    except mysql.connector.IntegrityError:
        return "Email already exists"
    except Exception as e:
        return f"Registration error: {str(e)}"

# Streamlit UI
def main():
    st.set_page_config(
        page_title="Library Login",
        page_icon="📚",
        layout="centered"
    )
    
    # Initialize session state
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'page' not in st.session_state:
        st.session_state.page = "login"
    
    # Header
    st.title("📚 Library Portal Login")
    st.markdown("---")
    
    # Login/Register tabs
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.header("Member Login")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="your.email@example.com")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if not email or not password:
                    st.error("Please fill in all fields")
                else:
                    user = login_user(email, password)
                    if user:
                        st.session_state.user = user
                        st.success(f"Welcome back, {user['name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid email or password")
    
    with tab2:
        st.header("New Member Registration")
        
        with st.form("register_form"):
            name = st.text_input("Full Name", placeholder="John Doe")
            email = st.text_input("Email", placeholder="your.email@example.com")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            membership_number = st.text_input("Membership Number (optional)", placeholder="LIB12345")
            submit = st.form_submit_button("Register")
            
            if submit:
                if not all([name, email, password, confirm_password]):
                    st.error("Please fill in all required fields")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    result = register_user(name, email, password, membership_number)
                    if "successful" in result:
                        st.success(result)
                    else:
                        st.error(result)
    
    # Footer
    st.markdown("---")
    st.caption("© 2024 Library Management System | For assistance, contact support@library.com")

if __name__ == "__main__":
    main()
