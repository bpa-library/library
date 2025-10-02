# streamlit_app/components/navigation.py
import streamlit as st
# from admin import admin_dashboard, uploads, books, users, analytics

def user_navigation():
    """User navigation sidebar"""
    st.sidebar.title("📚 Audio Library")
    # st.sidebar.title("Navigation")
    
    if 'menu_option' not in st.session_state:
        st.session_state.menu_option = "Browse Books"
    
    menu_option = st.sidebar.radio(
        "Menu",
        ["Browse Books", "My Library", "Profile"],
        index=["Browse Books", "My Library", "Profile"].index(st.session_state.menu_option)
        # ["Browse Books", "My Library", "Search", "Profile"],
        # index=["Browse Books", "My Library", "Search", "Profile"].index(st.session_state.menu_option)
    )
    
    if menu_option != st.session_state.menu_option:
        st.session_state.menu_option = menu_option
        st.rerun()
    
    return st.session_state.menu_option


def admin_navigation():
    """Admin navigation sidebar"""
    st.sidebar.title("Admin")

    # Use a dedicated session state variable for navigation
    if 'admin_nav_selection' not in st.session_state:
        st.session_state.admin_nav_selection = "Dashboard"

    nav_options = ["Dashboard", "Book Management", "User Management", "Audio Upload", "Analytics"]

    # Create the radio button
    selected_option = st.sidebar.radio(
        "Navigation",
        nav_options,
        index=nav_options.index(st.session_state.admin_nav_selection),
        key="admin_nav_widget_unique"
    )

    if selected_option != st.session_state.admin_nav_selection:
        st.session_state.admin_nav_selection = selected_option
        # Use a small delay to ensure state is updated
        import time
        time.sleep(0.1)
        st.rerun()

    return st.session_state.admin_nav_selection


# def admin_navigation():
#     """Admin navigation sidebar"""

#     # Admin menu
#     st.sidebar.title("Admin")

#     # use existing value or default once
#     # admin_option = st.session_state.get("admin_option", "Dashboard")

#     if 'admin_option' not in st.session_state:
#         st.session_state.admin_option = "Dashboard"

#     # Define the navigation options
#     nav_options = ["Dashboard", "Book Management", "User Management", "Audio Upload", "Analytics"]

#     def on_nav_change():
#         # This will be called when the radio selection changes
#         st.session_state.admin_option = st.session_state.admin_nav_radio

#     admin_option = st.sidebar.radio(
#         "Navigation",
#         nav_options,
#         index=nav_options.index(st.session_state.admin_option),
#         key="admin_option"
#         # key="admin_nav_radio",
#         # on_change=on_nav_change
#     )
#     # admin_option = st.sidebar.radio(
#     #     "Navigation",
#     #     ["Dashboard", "Book Management", "User Management", "Audio Upload", "Analytics"],
#     #     index=["Dashboard", "Book Management", "User Management", "Audio Upload", "Analytics"].index(current_value),
#     #     key="admin_nav_radio",
#     # )
#     # st.session_state.admin_option = admin_option

#     # current_value = st.session_state.get("admin_option", "Dashboard")
#     # print(f"st.session_state.admin_option = {st.session_state.admin_option}")
#     return admin_option


    # admin_option = st.sidebar.radio(
    #     "Navigation",
    #     ["Dashboard", "Book Management", "User Management", "Audio Upload", "Analytics"],
    #     index=["Dashboard", "Book Management", "User Management", "Audio Upload", "Analytics"].index(st.session_state.admin_option)
    # )
    
    # if admin_option != st.session_state.admin_option:
    #     st.session_state.admin_option = admin_option
    #     st.rerun()
    
    # return st.session_state.admin_option


# st.session_state.admin_action = 'upload_audio'