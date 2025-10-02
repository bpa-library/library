# streamlit_app/admin/dashboard.py
import streamlit as st
# from .library import my_library
# from .browse import browse_books
# from .profile import user_profile
from components.navigation import admin_navigation
# from user.dashboard import user_dashboard
# from admin.admin_dashboard import admin_dashboard
# from admin.uploads import upload_audio
from admin import admin_dashboard, uploads, admin_users #, books, analytics
# from auth import login


def admin_panel():
    """Admin panel - only accessible to admin users"""

    if 'admin_initialized' not in st.session_state:
        st.session_state.admin_initialized = True
        st.session_state.admin_nav_selection = "Dashboard"

    st.title("👨‍💼 Admin Dashboard")

    # Get the navigation selection
    option = admin_navigation()

    # Admin info
    if st.session_state.get('user_info'):
        user = st.session_state.user_info
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**Admin:** {user.get('name')}")
        st.sidebar.markdown(f"**Role:** {user.get('role')}")

    # Debug info (optional)
    if st.sidebar.checkbox("Show debug info", value=False):
        st.sidebar.write(f"Current option: {option}")
        st.sidebar.write(f"Session state nav: {st.session_state.get('admin_nav_selection')}")
        st.sidebar.write(f"User info exists: {'user_info' in st.session_state}")


    # Route based on selected option
    if option == "Dashboard":
        admin_dashboard.admin_dashboard()
    elif option == "Book Management":
        st.info("📚 Book Management section - to be implemented")
        st.write("This section will allow you to manage books in the library.")
    elif option == "User Management":
        admin_users.user_management()
        # st.info("👥 User Management section - to be implemented") 
        st.write("This section will allow you to manage user accounts and permissions.")
    elif option == "Audio Upload":
        uploads.upload_audio()
    elif option == "Analytics":
        st.info("📊 Analytics section - to be implemented")
        st.write("This section will show usage statistics and analytics.")

    # Add a debug section at the bottom of the page
    # with st.expander("Debug Information"):
    #     st.write(f"Current navigation option: {option}")
    #     st.write(f"admin_nav_selection session state: {st.session_state.get('admin_nav_selection')}")
    #     st.write(f"All session state keys: {list(st.session_state.keys())}")

    # Logout button
    st.sidebar.markdown("---")

    with st.sidebar.form(key="logout_form"):
        if st.form_submit_button("🚪 Logout", use_container_width=True):
            # Clear session state safely
            keys_to_remove = ['user_token', 'user_info', 'admin_nav_selection', 'admin_initialized']
            for key in keys_to_remove:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()


# def admin_panel():
#     """Admin panel - only accessible to admin users"""

#     st.title("👨‍💼 Admin Dashboard")
    
#     # Verify admin role again for security
#     # try:
#     #     decoded = jwt.decode(st.session_state.user_token, 
#     #                        os.getenv('JWT_SECRET', 'fallback-secret'), 
#     #                        algorithms=['HS256'])
        
#     #     if decoded.get('role') != 'admin':
#     #         st.error("Access denied. Admin privileges required.")
#     #         user_dashboard()
#     #         return
            
#     # except:
#     #     st.error("Invalid admin session.")
#     #     login()
#     #     return
    
#     # Admin menu

#     option = admin_navigation()

#     # Admin info (after nav, so sidebar content stacks nicely)
#     if st.session_state.get('user_info'):
#         user = st.session_state.user_info
#         st.sidebar.markdown("---")
#         st.sidebar.markdown(f"**Admin:** {user.get('name')}")
#         st.sidebar.markdown(f"**Role:** {user.get('role')}")

#     # Route based on selected option
#     if option == "Dashboard":
#         admin_dashboard.admin_dashboard()
#     elif option == "Book Management":
#         books.book_management()
#     elif option == "User Management":
#         users.user_management()
#     elif option == "Audio Upload":
#         uploads.upload_audio()
#     elif option == "Analytics":
#         analytics.analytics_page()

#     # Logout button
#     st.sidebar.markdown("---")
#     if st.sidebar.button("🚪 Logout"):
#         for key in ['user_token', 'user_info']:
#             if key in st.session_state:
#                 del st.session_state[key]
#         st.rerun()



def search_booksXX():
    """Search functionality"""
    # Your search logic here
    pass