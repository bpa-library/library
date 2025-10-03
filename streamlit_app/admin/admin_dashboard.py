# streamlit_app/admin/admin_dashboard.py
import streamlit as st
import requests
from config import API_URL
# from admin.uploads import upload_audio

###########
def admin_dashboard():
    """Main admin dashboard with overview and quick actions"""
    # st.title("🏠 Admin Dashboard")

    if 'dashboard_loading' not in st.session_state:
        st.session_state.dashboard_loading = False

    def navigate_to(section):
        """Navigation helper function with loading state"""
        st.session_state.dashboard_loading = False #True
        st.session_state.admin_nav_selection = section
        st.rerun()
    
    # If we're in a loading state, show spinner and return early
    if st.session_state.dashboard_loading:
        with st.spinner("Navigating..."):
            # Small delay to ensure navigation happens
            import time
            time.sleep(0.1)
            st.session_state.dashboard_loading = False
        return
    
    if st.session_state.get('user_info'):
        user = st.session_state.user_info
        st.success(f"Welcome back, {user['name']} ({user['email']})")
    # Display welcome message with admin info
    # if st.session_state.get('admin_user'):
    #     user = st.session_state.admin_user
    #     st.success(f"Welcome back, {user['name']} ({user['email']})")
    
    # Quick stats cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_books = get_total_books()
        st.metric("📚 Total Books", total_books)
    
    with col2:
        total_users = get_total_users()
        st.metric("👥 Total Users", total_users)
    
    with col3:
        total_chapters = get_total_chapters()
        st.metric("🎵 Total Chapters", total_chapters)

    # with col4:
    #     # pending_uploads = get_pending_uploads()
    #     # st.metric("⏳ Pending Uploads", pending_uploads)
    #     pass

    
    st.markdown("---")
    
    # Quick actions
    # st.subheader("🚀 Quick Actions")
    
    # quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)

    
    
    # with quick_col1:
    #     if st.button("📖 Add New Book", use_container_width=True, key="quick_book_1"):
    #         st.session_state.admin_nav_selection = "Book Management"
    #         st.rerun()
    
    # with quick_col2:
    #     if st.button("🎵 Upload Audio", use_container_width=True, key="quick_audio_1"):
    #         navigate_to("Audio Upload") 
    #         # st.session_state.admin_nav_selection = "Audio Upload"
    #         # st.rerun()


    # # with quick_col2:
    # #     # ONLY ONE Upload Audio button with unique key
    # #     if st.button("🎵 Upload Audio", use_container_width=True, key="quick_audio"):
    # #         st.query_params["nav"] = "Audio Upload"
    # #         st.rerun()
    
    # with quick_col3:
    #     if st.button("👥 Manage Users", use_container_width=True, key="quick_users_1"):
    #         st.session_state.admin_nav_selection = "User Management"
    #         st.rerun()
            
    # with quick_col4:
    #     if st.button("📊 View Analytics", use_container_width=True, key="quick_analytics_1"):
    #         st.session_state.admin_nav_selection = "Analytics"
    #         st.rerun()
    
    st.markdown("---")
    
    # Recent activity sections
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📈 System Health")

        db_status = check_database_status()
        st.write(f"**Database:** {'✅ Connected' if db_status else '❌ Disconnected'}")

        b2_status = check_backblaze_status()
        st.write(f"**Backblaze B2:** {'✅ Connected' if b2_status else '❌ Disconnected'}")

        storage = get_storage_usage()
        if storage.get("success"):
            used = storage["used_gb"]
            quota = storage["quota_gb"]
            ratio = storage["usage_ratio"]
            st.write(f"**Storage Usage:** {used}GB / {quota}GB")
            st.progress(ratio)
        else:
            st.warning(f"Storage check failed: {storage.get('error')}")
    
    st.markdown("---")
    
    # Admin tools section
    st.subheader("🛠️ Admin Tools")
    
    tool_col1, tool_col2, tool_col3 = st.columns(3)
    
    # with tool_col1:
    #     if st.button("🔄 Sync Database", help="Synchronize database indexes"):
    #         if sync_database():
    #             st.success("Database synced successfully")
    #         else:
    #             st.error("Database sync failed")
    
    # with tool_col2:
    #     if st.button("🧹 Clear Cache", help="Clear application cache"):
    #         clear_cache()
    #         st.success("Cache cleared")
    
    with tool_col3:
        if st.button("📋 Export Data", help="Export database to CSV"):
            # export_data()
            st.info("Export data - to be implemented")
            st.write("This section will allow you to manage export in the library.")
            #st.success("Data exported successfully")



def get_total_books():
    try:
        resp = requests.get(f"{API_URL}/api/get-total-books", timeout=5)
        data = resp.json()
        return data.get("count", 0) if resp.status_code == 200 else 0
    except Exception as e:
        print(f"❌ Error fetching total books: {e}")
        return 0

def get_total_users():
    try:
        resp = requests.get(f"{API_URL}/api/get-total-users", timeout=5)
        data = resp.json()
        return data.get("count", 0) if resp.status_code == 200 else 0
    except Exception as e:
        print(f"❌ Error fetching total users: {e}")
        return 0

def get_total_chapters():
    try:
        resp = requests.get(f"{API_URL}/api/get-total-chapters", timeout=5)
        data = resp.json()
        return data.get("count", 0) if resp.status_code == 200 else 0
    except Exception as e:
        print(f"❌ Error fetching total chapters: {e}")
        return 0


def check_database_status():
    """Streamlit function to check DB via API"""
    try:
        response = requests.get(f"{API_URL}/api/check_database_status")
        if response.status_code == 200:
            return response.json().get("database_connected", False)
        return False
    except Exception as e:
        st.error(f"Error checking database status: {e}")
        return False


def check_backblaze_status():
    """Streamlit function to check Backblaze via API"""
    try:
        response = requests.get(f"{API_URL}/api/check_backblaze_status")
        if response.status_code == 200:
            return response.json().get("backblaze_connected", False)
        return False
    except Exception as e:
        st.error(f"Error checking Backblaze status: {e}")
        return False

def get_storage_usage():
    try:
        resp = requests.get(f"{API_URL}/api/get-storage-usage", timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"success": False, "error": f"Status {resp.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}



