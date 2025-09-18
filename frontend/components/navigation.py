# streamlit_app/components/navigation.py
import streamlit as st

def user_navigation():
    """User navigation sidebar"""
    st.sidebar.title("Navigation")
    
    if 'menu_option' not in st.session_state:
        st.session_state.menu_option = "Browse Books"
    
    menu_option = st.sidebar.radio(
        "Menu",
        ["Browse Books", "My Library", "Search", "Profile"],
        index=["Browse Books", "My Library", "Search", "Profile"].index(st.session_state.menu_option)
    )
    
    if menu_option != st.session_state.menu_option:
        st.session_state.menu_option = menu_option
        st.rerun()
    
    return st.session_state.menu_option

def admin_navigation():
    """Admin navigation sidebar"""
    # Admin navigation logic here
    pass