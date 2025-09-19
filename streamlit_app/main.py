# streamlit_app/main.py
import streamlit as st
from auth import auth_page, check_authentication
from config import API_URL, DEBUG  # Import from config
# from admin.dashboard import admin_panel
from user.dashboard import user_dashboard

# API_URL = "https://library-11.vercel.app"  # Your Flask API
# API_URL = "http://localhost:8000"  # Use localhost for development

def main():
    st.set_page_config(
        page_title="Audio Library",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    if DEBUG:
        st.sidebar.info(f"Debug mode: {DEBUG}")
        st.sidebar.info(f"API: {API_URL}")
    
    # Check authentication and route accordingly
    user_info = check_authentication()
    
    if not user_info:
        auth_page()
    elif user_info.get('role') == 'admin':
        # admin_panel()
        pass
    else:
        user_dashboard()


if __name__ == "__main__":
    main()