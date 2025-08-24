import streamlit as st
import requests
import urllib.parse
from datetime import datetime, timedelta  # Uncomment and fix this import
import time
import jwt
import os

API_URL = "https://library-11.vercel.app"  # Your Flask API
#API_URL = "http://localhost:8000"  # Use localhost for development


def login_user(email, password):
    try:
        response = requests.post(f"{API_URL}/", json={
            "email": email,
            "password": password
        })
        
        if response.status_code == 200:
            return response.json()
        else:
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

def get_signed_audio_url(book_id, chapter_title):
    """Get signed URL from Flask API"""
    try:

        response = requests.get(
            f"{API_URL}/api/audio-url/{book_id}/{chapter_title}",  # No encoding
            timeout=10
        )
        # Use the original audio-url endpoint, NOT the streaming one
        # encoded_title = urllib.parse.quote(chapter_title)
        # response = requests.get(
        #     f"{API_URL}/api/audio-url/{book_id}/{encoded_title}",
        #     timeout=10
        # )
        
        if response.status_code == 200:
            data = response.json()
            url = data.get('url')
            
            # Debug: Check the URL
            print(f"Generated signed URL: {url}")
            

            # import threading
            # def test_url_background():
            #     try:
            #         test_response = requests.head(url, timeout=5)
            #         if test_response.status_code == 200:
            #             print("✅ URL is accessible")
            #         else:
            #             print(f"❌ URL access failed: {test_response.status_code}")
            #     except:
            #         pass  # Silent fail for background test
            
            # threading.Thread(target=test_url_background).start()

            # Test if the URL is accessible (but don't block on this)
            # try:
            #     test_response = requests.head(url, timeout=5)
            #     if test_response.status_code == 200:
            #         print("✅ URL is accessible")
            #     else:
            #         print(f"❌ URL access failed: {test_response.status_code}")
            # except Exception as test_e:
            #     print(f"❌ URL test error: {str(test_e)}")
            
            # Return the URL regardless - we know they work from browser tests
            return url
        else:
            st.error(f"Failed to get audio URL: {response.status_code}")
            print(f"API response: {response.text}")
            return None
            
    except Exception as e:
        st.error(f"Error getting audio URL: {str(e)}")
        print(f"Exception: {str(e)}")
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
                    with st.expander(f"{book['title']} (ID: {book['id']})"):
                        st.write(f"**Book ID:** {book['id']}")
                        
                        if book.get('chapters'):
                            for chapter in book['chapters']:
                                col1, col2 = st.columns([2, 3])
                                
                                with col1:
                                    st.write(f"**Chapter {chapter['chapter_number']}:**")
                                    st.write(chapter['title'])
                                
                                with col2:
                                    # Create a unique key for each audio player
                                    audio_key = f"audio_{book['id']}_{chapter['chapter_number']}"
                                    
                                    if st.button(f"Load Audio", key=f"btn_{audio_key}"):
                                        with st.spinner("Generating audio URL..."):
                                            audio_url = get_signed_audio_url(book['id'], chapter['title'])
                                        
                                        if audio_url:
                                            # Use HTML audio component instead of st.audio
                                            try:
                                                audio_html = f'''
                                                <div style="margin: 10px 0;">
                                                    <audio controls style="width: 100%; max-width: 400px;">
                                                        <source src="{audio_url}" type="audio/mpeg">
                                                        Your browser does not support the audio element.
                                                    </audio>
                                                    <div style="margin-top: 5px; font-size: 12px;">
                                                        <a href="{audio_url}" target="_blank">Open in new tab</a>
                                                    </div>
                                                </div>
                                                '''
                                                st.components.v1.html(audio_html, height=100)
                                            except Exception as html_error:
                                                st.error(f"Audio player error: {html_error}")
                                                # Fallback: provide download link
                                                st.download_button(
                                                    label="Download Audio",
                                                    data=requests.get(audio_url).content,
                                                    file_name=f"{chapter['title']}.mp3",
                                                    mime="audio/mp3"
                                                )
                                        else:
                                            st.error("Failed to load audio")
                        
                        st.divider()
            else:
                st.info("No books available in the library yet.")
        else:
            st.error("Failed to load books from database")
    except Exception as e:
        st.error(f"Failed to load books: {str(e)}")



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
                    if result and isinstance(result, dict):
                        if result.get('success'):
                            st.session_state.user = result['user']
                            st.session_state.token = result['token']
                            st.success(f"Welcome back, {result['user']['name']}!")
                            time.sleep(1)
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

# If you need to generate JWT tokens elsewhere in your app, add this function:
def generate_jwt_token(user_data):
    """Generate JWT token for a user"""
    try:
        token = jwt.encode(
            {
                'user_id': user_data['id'],
                'email': user_data['email'], 
                'role': user_data['role'],
                'exp': datetime.utcnow() + timedelta(hours=24)
            },
            os.getenv('JWT_SECRET', 'fallback-secret'),
            algorithm='HS256'
        )
        return token
    except Exception as e:
        st.error(f"Error generating token: {str(e)}")
        return None

def main():
    st.set_page_config(
        page_title="Library Portal",
        page_icon="📚",
        layout="wide"
    )
    
    # Initialize session state
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'token' not in st.session_state:
        st.session_state.token = None
    
    # Simple header
    st.sidebar.title("Library Portal")
    
    if st.sidebar.button("Refresh Data"):
        st.rerun()
    
    # Show dashboard if logged in, else show login
    if st.session_state.user:
        dashboard()
        if st.sidebar.button("Logout"):
            st.session_state.user = None
            st.session_state.token = None
            st.rerun()
    else:
        show_login_register()

if __name__ == "__main__":
    main()