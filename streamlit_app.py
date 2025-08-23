import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta

API_URL = "https://library-11.vercel.app"  # Your Flask API


def login_user(email, password):
    try:
        response = requests.post(f"{API_URL}/", json={
            "email": email,
            "password": password
        })
        
        if response.status_code == 200:
            return response.json()
        else:
            # Return a proper error structure
            try:
                error_data = response.json()
                return {"success": False, "error": error_data.get('error', 'Login failed')}
            except:
                return {"success": False, "error": f"Login failed with status {response.status_code}"}
                
    except Exception as e:
        return {"success": False, "error": f"Connection error: {str(e)}"}

def register_user(name, email, password, membership_number=None):
    try:
        response = requests.post(f"{API_URL}/api/register", json={
            "name": name,
            "email": email,
            "password": password,
            "membership_number": membership_number
        })
        return response.json()
    except Exception as e:
        return {"error": f"Connection failed: {str(e)}"}

# def get_audio_url(book_title, chapter_title):
#     """Use S3-compatible URL"""
#     encoded_book = urllib.parse.quote(book_title)
#     encoded_chapter = urllib.parse.quote(chapter_title)
    
#     return f"https://audiobooks-free.s3.us-east-005.backblazeb2.com/{encoded_book}/{encoded_chapter}"

def get_audio_url(book_title, chapter_title):
    """Try alternative public URL format"""
    encoded_book = urllib.parse.quote(book_title)
    encoded_chapter = urllib.parse.quote(chapter_title)
    
    return f"https://f005.backblazeb2.com/file/audiobooks-free/{encoded_book}/{encoded_chapter}"

# def get_audio_url(book_title, chapter_title):
#     """Generate Backblaze B2 audio URL"""
#     # URL encode the titles (Backblaze uses + for spaces in friendly URLs)
#     encoded_book = urllib.parse.quote(book_title.replace(' ', '+'))
#     encoded_chapter = urllib.parse.quote(chapter_title.replace(' ', '+'))
    
#     return f"https://f005.backblazeb2.com/file/audiobooks-free/{encoded_book}/{encoded_chapter}"

def get_signed_audio_url(book_id, chapter_title):
    """Get signed URL from Flask API"""
    try:
        response = requests.get(
            f"{API_URL}/api/audio-url/{book_id}/{chapter_title}",
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get('url')
        else:
            return None
    except:
        return None

def dashboard():
    st.title("📚 Audio Book Library")
    st.subheader("Browse Available Books")

    try:
        response = requests.get(f"{API_URL}/books", timeout=10)
        if response.status_code == 200:
            data = response.json()
            books = data.get("books", [])
            
            if books:
                for book in books:
                    with st.expander(f"{book['title']}"):
                        st.write(f"**Book ID:** {book['id']}")
                        
                        if book.get('chapters'):
                            for chapter in book['chapters']:
                                st.write(f"**Chapter {chapter['chapter_number']}:** {chapter['title']}")
                                
                                # Get signed URL
                                audio_url = get_signed_audio_url(book['id'], chapter['title'])
                                
                                if audio_url:
                                    st.audio(audio_url, format="audio/mp3")
                                else:
                                    st.warning("Could not load audio")
                                
                                st.divider()
            else:
                st.info("No books available yet.")
    except Exception as e:
        st.error(f"Failed to load books: {str(e)}")

# def dashboard():
#     st.title("📚 Audio Book Library")
#     st.subheader("Browse Available Books")

#     try:
#         response = requests.get(f"{API_URL}/books", timeout=10)
#         if response.status_code == 200:
#             data = response.json()
#             books = data.get("books", [])
            
#             if books:
#                 for book in books:
#                     with st.expander(f"{book['title']}"):
#                         st.write(f"**Book ID:** {book['id']}")
                        
#                         # Display chapters
#                         if book.get('chapters'):
#                             for chapter in book['chapters']:
#                                 st.write(f"**Chapter {chapter['chapter_number']}:** {chapter['title']}")
                                
#                                 # Generate audio URL
#                                 audio_url = get_audio_url(book['title'], chapter['title'])
                                
#                                 # Display audio player
#                                 st.audio(audio_url, format="audio/mp3")
#                                 st.write(f"URL: {audio_url}")  # For debugging
                                
#                                 st.divider()
#                         else:
#                             st.info("No chapters available for this book.")
#             else:
#                 st.info("No books available in the library yet.")
#         else:
#             st.error("Failed to load books from database")
#     except Exception as e:
#         st.error(f"Failed to load books: {str(e)}")

# def dashboard():
#     st.title("📚 Audio Book Library")
#     st.subheader("Browse Available Books")

#     try:
#         response = requests.get(f"{API_URL}/books", timeout=10)
#         if response.status_code == 200:
#             data = response.json()
#             books = data.get("books", [])
            
#             if books:
#                 for book in books:
#                     # Create an expander for each book
#                     with st.expander(f"{book['title']} (ID: {book['id']})"):
#                         st.write(f"**Book ID:** {book['id']}")
#                         st.write(f"**Total Chapters:** {len(book.get('chapters', []))}")
                        
#                         # Display chapters
#                         if book.get('chapters'):
#                             st.subheader("Chapters:")
#                             for chapter in book['chapters']:
#                                 col1, col2, col3 = st.columns([1, 3, 2])
#                                 with col1:
#                                     st.write(f"**{chapter['chapter_number']}**")
#                                 with col2:
#                                     st.write(chapter['title'])
#                                 with col3:
#                                     # Audio player for each chapter
#                                     audio_url = f"https://your-b2-url/{book['id']}/chapter_{chapter['chapter_number']}.mp3"
#                                     st.audio(audio_url, format="audio/mp3")
#                         else:
#                             st.info("No chapters available for this book.")
#             else:
#                 st.info("No books available in the library yet.")
#         else:
#             st.error("Failed to load books from database")
#     except Exception as e:
#         st.error(f"Failed to load books: {str(e)}")

# def dashboard():
#     st.title("📚 Audio Book Library")
#     st.subheader("Browse Available Books")

#     # Fetch data from Flask API
#     try:
#         response = requests.get(f"{API_URL}/books")
#         if response.status_code == 200:
#             books = response.json().get("books", [])
#             for book in books:
#                 with st.expander(book['title']):
#                     st.write(f"ID: {book['id']}")
#                     # Replace with your actual audio URL logic
#                     st.audio(f"https://your-b2-url/{book['id']}.mp3")  
#         else:
#             st.error("Failed to load books from database")
#     except Exception as e:
#         st.error(f"API connection error: {str(e)}")

# Streamlit UI
def main():
    st.set_page_config(
        page_title="Library Portal",
        page_icon="📚",
        layout="centered"
    )
    
    # Initialize session state
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'token' not in st.session_state:
        st.session_state.token = None
    
    # Show dashboard if logged in, else show login
    if st.session_state.user:
        dashboard()
        if st.button("Logout"):
            st.session_state.user = None
            st.session_state.token = None
            st.rerun()
    else:
        show_login_register()

def show_login_register():
    st.title("📚 Library Portal Login")
    st.markdown("---")
    
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
                    result = login_user(email, password)
                    # Check if result exists and has the expected structure
                    if result and isinstance(result, dict):
                        if result.get('success'):
                            st.session_state.user = result['user']
                            st.session_state.token = result['token']
                            st.success(f"Welcome back, {result['user']['name']}!")
                            st.rerun()
                        else:
                            st.error(result.get('error', 'Login failed'))
                    else:
                        st.error("Unexpected response from server")

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
                    if result.get('success'):
                        st.success("Registration successful! Please login.")
                    else:
                        st.error(result.get('error', 'Registration failed'))

if __name__ == "__main__":
    main()