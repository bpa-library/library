# streamlit_app/admin/admin_users.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from config import API_URL, DEBUG
# import plotly.express as px
from auth import register
import os
from dotenv import load_dotenv
load_dotenv()

def user_management():
    """User Management section for admin panel"""
    
    st.header("👥 User Management")
    
    # Check if user is admin
    if st.session_state.get('user_info', {}).get('role') != 'admin':
        st.error("⛔ Access denied. Admin privileges required.")
        return
    
    # Tab interface for different user management tasks
    tab1, tab2 = st.tabs(["👥 View Users", "➕ Add User"])
    # tab1, tab2, tab3 = st.tabs(["👥 View Users", "➕ Add User", "📊 User Analytics"])
    
    with tab1:
        view_users()
    
    with tab2:
        add_user()
    
    # with tab3:
    #     user_analytics()

def view_users():
    st.subheader("All Users")

    # Search and filter
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_query = st.text_input("🔍 Search users by name or email", key="user_search")
    with col2:
        role_filter = st.selectbox("Filter by role", ["All", "member", "admin"], key="role_filter")
    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    users = get_users_from_api(search_query, role_filter)

    if users:
        for user in users:
            with st.expander(f"👤 {user['name']} ({user['email']})", expanded=False):
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.write(f"**User ID:** {user['id']}")
                    st.write(f"**Role:** {user['role']}")
                    st.write(f"**Membership Number:** {user.get('membership_number', 'N/A')}")

                with col2:
                    new_role = st.selectbox(
                        "Change role",
                        ["member", "admin"],
                        index=0 if user['role'] == 'member' else 1,
                        key=f"role_{user['id']}"
                    )
                    if st.button("Update Role", key=f"update_{user['id']}"):
                        if update_user_role(user['id'], new_role):
                            st.success("✅ Role updated successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to update role")

                with col3: # col3.right
                    # d2, d1 = st.columns([2, 2])
                    # with d2:
                        if st.button("🗑️ Delete User", key=f"delete_trigger_{user['id']}", type="secondary",):
                            st.session_state[f"confirm_delete_{user['id']}"] = True

                        # Show confirmation only if triggered
                        if st.session_state.get(f"confirm_delete_{user['id']}", False):
                            st.warning("🚨 **This action cannot be undone!**")
                            c1, c2 = st.columns(2)
                            with c1:
                                if st.button("✅ Confirm", key=f"confirm_{user['id']}"):
                                    if delete_user_api(user['id']):  # <- separate API call
                                        st.success("✅ User deleted successfully!")
                                        st.session_state[f"confirm_delete_{user['id']}"] = False
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to delete user")
                            with c2:
                                if st.button("❌ Cancel", key=f"cancel_{user['id']}"):
                                    st.session_state[f"confirm_delete_{user['id']}"] = False
                                    st.info("ℹ️ Deletion cancelled")

    else:
        st.info("ℹ️ No users found matching your criteria.")


def delete_user_api(user_id):
    """Call API to delete user (backend only, no UI widgets here)"""
    try:
        response = requests.delete(
            f"{API_URL}/admin/users/{user_id}",
            headers={'Authorization': f"Bearer {st.session_state.get('user_token', '')}"}
        )
        if response.status_code == 200:
            return response.json().get("success", False)
        return False
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return False


def add_user():
    """Tab for adding new users - uses the modified register function"""
    # Use the register function in admin mode
    result = register(admin_mode=True, default_role="member")
    
    # If user was successfully added, provide option to add another
    if result:
        if st.button("➕ Add Another User"):
            st.rerun()


def user_analytics():
    """Tab for user analytics"""
    
    st.subheader("User Analytics")
    
    try:
        response = requests.get(
            f"{API_URL}/admin/users/analytics",
            headers={'Authorization': f"Bearer {st.session_state.get('user_token', '')}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                analytics = data.get('analytics', {})
                
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("👥 Total Users", analytics.get('total_users', 0))
                
                with col2:
                    st.metric("👑 Admin Users", analytics.get('admin_count', 0))
                
                with col3:
                    st.metric("👤 Member Users", analytics.get('member_count', 0))
                
                with col4:
                    st.metric("🆕 Recent Signups (30d)", analytics.get('recent_signups', 0))
                
                # Role distribution chart
                if analytics.get('total_users', 0) > 0:
                    role_data = {
                        'Role': ['Admin', 'Member'],
                        'Count': [analytics.get('admin_count', 0), analytics.get('member_count', 0)]
                    }
                    
                    df = pd.DataFrame(role_data)
                    fig = px.pie(df, values='Count', names='Role', title='📈 User Role Distribution',color='Role', 
                                 color_discrete_map={'Admin': '#FF6B6B', 'Member': '#4ECDC4'})
                    st.plotly_chart(fig, use_container_width=True)

                    st.info(f"ℹ️ **Quick Stats:**"
                          f"\n- Admins make up {((analytics.get('admin_count', 0) / analytics.get('total_users', 1)) * 100):.1f}% of users"
                          f"\n- {analytics.get('recent_signups', 0)} new users joined in the last 30 days")
                
                # Additional analytics can be added here
                # st.info("More detailed analytics will be available as the user base grows.")
                else:
                    st.warning("⚠️ No user data available yet")
            
            else:
                st.error(f"❌ Error loading analytics: {data.get('error', 'Unknown error')}")
        
        else:
            st.error("❌ Failed to load analytics from server")
    
    except Exception as e:
        st.error(f"❌ Error loading analytics: {str(e)}")


def get_users_from_api(search_query=None, role_filter="All"):
    """Get users from API with optional filters"""
    try:
        params = {}
        if search_query:
            params['search'] = search_query
        if role_filter != "All":
            params['role'] = role_filter
        
        response = requests.get(
            f"{API_URL}/admin/users",
            headers={'Authorization': f"Bearer {st.session_state.get('user_token', '')}"},
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('users', [])
            else:
                st.error(f"❌ API Error: {data.get('error', 'Unknown error')}")
        
        return []
    
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to server. Please check your connection.")
        return []
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return []

def update_user_role(user_id, new_role):
    """Update user role via API"""
    try:
        response = requests.put(
            f"{API_URL}/admin/users/{user_id}/role",
            headers={
                'Authorization': f"Bearer {st.session_state.get('user_token', '')}",
                'Content-Type': 'application/json'
            },
            json={'role': new_role}
        )
        
        if response.status_code == 200:
            data = response.json()
            if st.success(f"✅ Update success)"):       #data.get('success'):
                return True
            else:
                st.error(f"❌ {data.get('error', 'Failed to update role')}")
        elif response.status_code == 404:
            st.error("❌ User not found")
        else:
            st.error("❌ Server error occurred")

        return False
    
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to server. Please check your connection.")
        return False
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return False


def delete_user(user_id):
    """Delete user via API"""
    current_user_id = st.session_state.get('user_info', {}).get('id')
    if user_id == current_user_id:
        st.error("🚫 You cannot delete your own account!")
        return False

    # Initialize confirmation state
    confirm_key = f"confirm_delete_{user_id}"
    if confirm_key not in st.session_state:
        st.session_state[confirm_key] = False

    # First click → ask for confirmation
    if not st.session_state[confirm_key]:
        if st.button("🗑️ Delete User", key=f"delete_{user_id}", type="secondary"):
            st.session_state[confirm_key] = True
            st.rerun()
        return False
    else:
        # Show confirmation UI
        st.warning("🚨 **This action cannot be undone!**")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Confirm Deletion", key=f"confirm_btn_{user_id}"):
                try:
                    with st.spinner("🗑️ Deleting user..."):
                        response = requests.delete(
                            f"{API_URL}/admin/users/{user_id}",
                            headers={'Authorization': f"Bearer {st.session_state.get('user_token', '')}"}
                        )
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('success'):
                            st.success("✅ User deleted successfully!")
                            # reset confirmation
                            st.session_state[confirm_key] = False
                            st.rerun()
                            return True
                        else:
                            st.error(f"❌ {data.get('error', 'Failed to delete user')}")
                    elif response.status_code == 400:
                        st.error(response.json().get('error', 'Cannot delete user'))
                    elif response.status_code == 404:
                        st.error("❌ User not found")
                    else:
                        st.error("❌ Server error occurred")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to server. Please check your connection.")
                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")
                st.session_state[confirm_key] = False
                return False

        with col2:
            if st.button("❌ Cancel", key=f"cancel_btn_{user_id}"):
                st.info("ℹ️ Deletion cancelled")
                st.session_state[confirm_key] = False
                st.rerun()
        return False

