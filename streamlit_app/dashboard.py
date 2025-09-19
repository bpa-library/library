# streamlit_app/user/dashboard.py
import streamlit as st
# from .library import my_library
from .browse import browse_books
# from .profile import user_profile
from components.navigation import user_navigation

def user_dashboard():
    """Regular user dashboard"""
    st.title("📚 My Audio Library")
    
    # Get navigation selection
    menu_option = user_navigation()
    
    # Route to appropriate section
    if menu_option == "Browse Books":
        browse_books()
    elif menu_option == "My Library":
        pass
        # my_library()
    elif menu_option == "Search":
        pass
        # search_books()
    elif menu_option == "Profile":
        pass
        # user_profile()

def search_books():
    """Search functionality"""
    # Your search logic here
    pass