# streamlit_app/auth.py
import streamlit as st
import requests
from datetime import datetime, timedelta
from config import API_URL, DEBUG

def auth_page():
    """Authentication page with login and register tabs"""
    st.title("📚 Welcome to Audio Library")

    if DEBUG:
        st.sidebar.info(f"API Endpoint: {API_URL}")
    
    login()

    # tab1, tab2 = st.tabs(["Login", "Register"])
    
    # with tab1:
    #     login()
    # with tab2:
    #     # Public registration - always as 'member'
    #     register(admin_mode=False, default_role="member")


def login():
    """User login function"""
    st.header("Login to Your Account")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if not email or not password:
                st.error("Please enter both email and password")
                return
                
            try:
                if DEBUG:
                    st.info(f"Attempting login to: {API_URL}/api/login")

                response = requests.post(
                    f"{API_URL}/api/login",
                    json={"email": email, "password": password},
                    timeout=10
                )
                
                if DEBUG:
                    st.info(f"Response status: {response.status_code}")
                    st.info(f"Response text: {response.text}")
                    
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        # Store token and user info
                        st.session_state.user_token = data.get('token')
                        st.session_state.user_info = data.get('user')
                        
                        if data.get('user') and 'id' in data['user']:
                            st.session_state.user_id = data['user']['id']
                        
                        # Store token expiry if provided
                        if 'expires_in' in data:
                            st.session_state.token_expiry = datetime.now() + timedelta(seconds=data['expires_in'])
                        
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error(data.get('error', 'Login failed'))
                else:
                    st.error(f"Login failed: {response.status_code}")
                    
            except Exception as e:
                st.error(f"Connection error: {str(e)}")

# # def login():
#     """User login function"""
#     st.header("Login to Your Account")
    
#     with st.form("login_form"):
#         email = st.text_input("Email")
#         password = st.text_input("Password", type="password")
        
#         if st.form_submit_button("Login"):
#             try:
#                 response = requests.post(
#                     f"{API_URL}/",
#                     json={"email": email, "password": password},
#                     timeout=10
#                 )
                
#                 if response.status_code == 200:
#                     data = response.json()
#                     if data.get('success'):
#                         # Store token and user info
#                         st.session_state.user_token = data.get('token')
#                         st.session_state.user_info = data.get('user')
                        
#                         # ✅ CRITICAL: Store user ID for database queries
#                         if data.get('user') and 'id' in data['user']:
#                             st.session_state.user_id = data['user']['id']
                        
#                         st.success("Login successful!")
#                         st.rerun()
#                     else:
#                         st.error(data.get('error', 'Login failed'))
#                 else:
#                     st.error(f"Login failed: {response.status_code}")
                    
#             except Exception as e:
#                 st.error(f"Connection error: {str(e)}")


def register(admin_mode=False, default_role="member"):
    if admin_mode:
        st.header("Add New User (Admin)")
    else:
        st.header("New Member Registration")

    # Initialize state
    if "register_success" not in st.session_state:
        st.session_state.register_success = False
        st.session_state.reg_pass = ""

    if st.session_state.register_success:
        st.success("✅ Registration successful!")
        if st.button("🔄 Register Another User"):
            st.session_state.register_success = False
            st.rerun()
        return
    
    with st.form("register_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", placeholder="John Doe", key="reg_name")
            email = st.text_input("Email", placeholder="your.email@example.com", key="reg_email")
            membership_number = st.text_input("Membership Number (optional)", placeholder="LIB12345", key="reg_membership")
        with col2:
            # print(f"st.session_state[key] = {key}")
            password = st.text_input("Password", type="password", key="reg_pass", value="")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_cpass")
            if admin_mode:
                role = st.selectbox(
                    "Role*", ["member", "admin"],
                    index=0 if default_role == "member" else 1,
                    key="reg_role"
                )
            else:
                role = default_role
        submit = st.form_submit_button("Create Account" if not admin_mode else "Add User")
        

        if submit:
            st.session_state.register_success = False  # reset

            if not all([name, email, password, confirm_password]):
                st.error("❌ Please fill in all required fields")
            elif password != confirm_password:
                st.error("❌ Passwords do not match")
            elif len(password) < 6:
                st.error("❌ Password must be at least 6 characters")
            else:
                result = register_user(name, email, password, membership_number, role)
                if result.get("success"):
                    st.session_state.register_success = True
                    st.rerun() 
                    return

                else:
                    st.error(result.get("error", "Registration failed"))

    # Show success message after rerun
    if st.session_state.register_success:
        st.success("✅ Registration successful! Please login!")



        
                    

def register_user(name, email, password, membership_number, role):
    try:
        response = requests.post(f"{API_URL}/api/register", json={
            "name": name,
            "email": email,
            "password": password,
            "role": role,
            "membership_number": membership_number
        })
        print(f"response.json() = {response.json()}")
        return response.json()
    except Exception as e:
        return {"error": f"Connection failed: {str(e)}"}




# def register(admin_mode=False, default_role="member"):
#     if admin_mode:
#         st.header("Add New User (Admin)")
#     else:
#         st.header("New Member Registration")

#     if 'clear_register_form' not in st.session_state:
#         st.session_state.register_form_cleared = False

#     form_key = "register_form_cleared" if st.session_state.register_form_cleared else "register_form"

#     # with st.form("register_form"):
#     with st.form(form_key, clear_on_submit=st.session_state.register_form_cleared):
#     # with st.form("register_form", clear_on_submit=True):
#         col1, col2 = st.columns(2)

#         with col1:
#             name = st.text_input("Full Name", placeholder="John Doe")
#             email = st.text_input("Email", placeholder="your.email@example.com")
#             membership_number = st.text_input("Membership Number (optional)", placeholder="LIB12345")

#         with col2:
#             password = st.text_input("Password", type="password")
#             confirm_password = st.text_input("Confirm Password", type="password")

#             if admin_mode:
#                 role = st.selectbox("Role*", ["member", "admin"], index=0 if default_role == "member" else 1)
#             else:
#                 role = default_role  # Public registration always uses default role

#         submit = st.form_submit_button("Create Account" if not admin_mode else "Add User")
        
#         if submit:
#             if not all([name, email, password, confirm_password]):
#                 st.error("❌ Please fill in all required fields")
#                 # st.session_state.clear_register_form = False
#             elif password != confirm_password:
#                 st.error("❌ Passwords do not match")
#                 # st.session_state.clear_register_form = False
#             elif len(password) < 6:
#                 st.error("❌ Password must be at least 6 characters")
#                 # st.session_state.clear_register_form = False
#             else:
#                 result = register_user(name, email, password, membership_number,role)
#                 if result.get('success'):
#                     st.success("✅ Registration successful! Please login.")
#                     st.session_state.clear_register_form = True
#                     st.rerun()
#                     # return True
#                 else:
#                     st.error(result.get('error', 'Registration failed'))
#                     # st.session_state.clear_register_form = False

#     if st.session_state.register_form_cleared:
#         st.session_state.register_form_cleared = False

# def register_user(name, email, password, membership_number, role):
#     try:
#         response = requests.post(f"{API_URL}/api/register", json={
#             "name": name,
#             "email": email,
#             "password": password,
#             "role": role,
#             "membership_number": membership_number
#         })
#         return response.json()
#     except Exception as e:
#         return {"error": f"Connection failed: {str(e)}"}


# def register(admin_mode=False, default_role="member"):
    """User registration function - can be used for both public and admin registration"""
    
    if admin_mode:
        st.header("Add New User (Admin)")
    else:
        st.header("Create New Account")
    
    with st.form("register_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name*")
            email = st.text_input("Email*")
        
        with col2:
            password = st.text_input("Password*", type="password")
            confirm_password = st.text_input("Confirm Password*", type="password")
            membership_number = st.text_input("Membership Number (optional)")
        
        # Only show role selection in admin mode
        if admin_mode:
            role = st.selectbox("Role*", ["member", "admin"], index=0 if default_role == "member" else 1)
        else:
            role = default_role  # Public registration always uses default role
        
        submitted = st.form_submit_button("Create Account" if not admin_mode else "Add User")
        
        if submitted:
            if password != confirm_password:
                st.error("Passwords do not match!")
                return False
            elif not all([name, email, password]):
                st.error("Please fill all required fields!")
                return False
            else:
                try:
                    # Use different endpoints for admin vs public registration
                    if admin_mode:
                        endpoint = f"{API_URL}/admin/users"
                        headers = {
                            'Authorization': f"Bearer {st.session_state.get('user_token', '')}",
                            'Content-Type': 'application/json'
                        }
                    else:
                        endpoint = f"{API_URL}/api/register"
                        headers = {'Content-Type': 'application/json'}
                    
                    response = requests.post(
                        endpoint,
                        headers=headers,
                        json={
                            "name": name,
                            "email": email,
                            "password": password,
                            "role": role,
                            "membership_number": membership_number
                        },
                        timeout=10
                    )
                    
                    if response.status_code in [200, 201]:
                        data = response.json()
                        if data.get('success'):
                            if admin_mode:
                                st.success("✅ User added successfully! 🎉")
                                st.balloons()
                            else:
                                # Set success flag for public registration
                                st.session_state.registration_success = True
                            return True
                        else:
                            st.error(data.get('error', 'Registration failed'))
                            return False
                    else:
                        st.error(f"Registration failed: {response.status_code}")
                        return False
                        
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")
                    return False
    return None



# def register():
#     """User registration function"""
#     st.header("Create New Account")
    
#     with st.form("register_form", clear_on_submit=True):
#         col1, col2 = st.columns(2)
        
#         with col1:
#             name = st.text_input("Full Name*")
#             email = st.text_input("Email*")
        
#         with col2:
#             password = st.text_input("Password*", type="password")
#             confirm_password = st.text_input("Confirm Password*", type="password")
#             membership_number = st.text_input("Membership Number (optional)")
        
#         submitted = st.form_submit_button("Create Account")
        
#         if submitted:
#             if password != confirm_password:
#                 st.error("Passwords do not match!")
#             elif not all([name, email, password]):
#                 st.error("Please fill all required fields!")
#             else:
#                 try:
#                     response = requests.post(
#                         f"{API_URL}/api/register",
#                         json={
#                             "name": name,
#                             "email": email,
#                             "password": password,
#                             "membership_number": membership_number
#                         },
#                         timeout=10
#                     )
                    
#                     if response.status_code == 200:
#                         data = response.json()
#                         if data.get('success'):
#                             # Set success flag and rerun to show message
#                             st.session_state.registration_success = True
#                             st.rerun()
#                         else:
#                             st.error(data.get('error', 'Registration failed'))
#                     else:
#                         st.error(f"Registration failed: {response.status_code}")
                        
#                 except Exception as e:
#                     st.error(f"Connection error: {str(e)}")

# streamlit_app/auth.py
def check_authentication():
    """Check if user is authenticated and token is valid"""
    
    if not st.session_state.get('user_info'):
        return None
    
    # Check if token exists
    token = st.session_state.get('user_token')
    if not token:
        return None
    
    # Verify token with backend
    try:
        response = requests.post(
            f"{API_URL}/api/verify-token",
            json={"token": token},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('valid'):
                # Update user info and token expiry
                user_info = data.get('user')
                if user_info:
                    st.session_state.user_info = user_info
                
                expires_in = data.get('expires_in')
                if expires_in:
                    st.session_state.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                
                return st.session_state.user_info
            else:
                st.warning("Session invalid. Please login again.")
                logout()
                return None
        else:
            # If token verification fails, continue with cached credentials
            return st.session_state.user_info
            
    except requests.exceptions.RequestException:
        # If API is unavailable, continue with cached credentials
        return st.session_state.user_info
    
########################################################################


def logout():
    """Clear user session data"""
    keys_to_remove = ['user_token', 'user_info', 'user_id', 'token_expiry']
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# def auth_page():
    """Authentication page with login and register tabs"""
    st.title("📚 Welcome to Audio Library")
    
    # Show success message after registration if needed
    if st.session_state.get('registration_success'):
        st.success("Registration successful! Please login with your credentials.")
        # Clear the success flag
        st.session_state.registration_success = False
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        login()
    with tab2:
        register()

# def login():
    # """User login function"""
    # st.header("Login to Your Account")
    
    # with st.form("login_form"):
    #     email = st.text_input("Email")
    #     password = st.text_input("Password", type="password")
    #     submitted = st.form_submit_button("Login")
        
    #     if submitted:
    #         if not email or not password:
    #             st.error("Please enter both email and password")
    #             return
                
    #         try:
    #             response = requests.post(
    #                 f"{API_URL}/api/login",  # Fixed the endpoint URL
    #                 json={"email": email, "password": password},
    #                 timeout=10
    #             )
                
    #             if response.status_code == 200:
    #                 data = response.json()
    #                 if data.get('success'):
    #                     # Store token and user info
    #                     st.session_state.user_token = data.get('token')
    #                     st.session_state.user_info = data.get('user')
                        
    #                     # ✅ CRITICAL: Store user ID for database queries
    #                     if data.get('user') and 'id' in data['user']:
    #                         st.session_state.user_id = data['user']['id']
                        
    #                     # Store token expiry if provided
    #                     if 'expires_in' in data:
    #                         st.session_state.token_expiry = datetime.now() + timedelta(seconds=data['expires_in'])
                        
    #                     st.success("Login successful!")
    #                     st.rerun()
    #                 else:
    #                     st.error(data.get('error', 'Login failed'))
    #             else:
    #                 st.error(f"Login failed: {response.status_code}")
                    
    #         except Exception as e:
    #             st.error(f"Connection error: {str(e)}")

# def register():
    """User registration function"""
    st.header("Create New Account")
    
    with st.form("register_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name*")
            email = st.text_input("Email*")
        
        with col2:
            password = st.text_input("Password*", type="password")
            confirm_password = st.text_input("Confirm Password*", type="password")
            membership_number = st.text_input("Membership Number (optional)")
        
        submitted = st.form_submit_button("Create Account")
        
        if submitted:
            if password != confirm_password:
                st.error("Passwords do not match!")
            elif not all([name, email, password]):
                st.error("Please fill all required fields!")
            else:
                try:
                    response = requests.post(
                        f"{API_URL}/api/register",
                        json={
                            "name": name,
                            "email": email,
                            "password": password,
                            "membership_number": membership_number
                        },
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('success'):
                            # Set success flag and rerun to show message
                            st.session_state.registration_success = True
                            st.rerun()
                        else:
                            st.error(data.get('error', 'Registration failed'))
                    else:
                        st.error(f"Registration failed: {response.status_code}")
                        
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")

# Optional: Add a logout button component
def logout_button():
    """Display logout button in sidebar"""
    if st.session_state.get('user_info'):
        with st.sidebar:
            if st.button("🚪 Logout"):
                logout()