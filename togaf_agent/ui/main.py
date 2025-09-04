"""
Main Streamlit application for TOGAF Agent UI.
"""

import streamlit as st
import requests
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd

from .components.onboarding import render_onboarding_flow
from .components.dashboard import render_dashboard
from .components.chat import render_chat_interface
from .components.learning_plan import render_learning_plan
from .utils.api_client import TOGAFAPIClient


# Page configuration
st.set_page_config(
    page_title="TOGAF Learning Agent",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .user-profile-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        text-align: center;
    }
    .success-message {
        color: #28a745;
        font-weight: bold;
    }
    .error-message {
        color: #dc3545;
        font-weight: bold;
    }
    .chat-message-user {
        background-color: #007bff;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 1rem;
        margin: 0.5rem 0;
        text-align: right;
    }
    .chat-message-agent {
        background-color: #f8f9fa;
        color: #333;
        padding: 0.5rem 1rem;
        border-radius: 1rem;
        margin: 0.5rem 0;
        border-left: 3px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application entry point."""
    
    # Initialize session state
    if "api_client" not in st.session_state:
        st.session_state.api_client = TOGAFAPIClient()
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = None
    if "page" not in st.session_state:
        st.session_state.page = "welcome"
    
    # Sidebar navigation
    render_sidebar()
    
    # Main content area
    if st.session_state.page == "welcome":
        render_welcome_page()
    elif st.session_state.page == "login":
        render_login_page()
    elif st.session_state.page == "register":
        render_register_page()
    elif st.session_state.page == "onboarding":
        render_onboarding_flow()
    elif st.session_state.page == "dashboard":
        render_dashboard()
    elif st.session_state.page == "chat":
        render_chat_interface()
    elif st.session_state.page == "learning_plan":
        render_learning_plan()
    elif st.session_state.page == "profile":
        render_profile_page()
    else:
        st.error("Page not found")

def render_sidebar():
    """Render the sidebar navigation."""
    with st.sidebar:
        st.markdown("## 🎯 TOGAF Agent")
        
        # User status
        if st.session_state.current_user:
            user = st.session_state.current_user
            with st.container():
                st.markdown(f"**Welcome, {user.get('username', 'User')}!**")
                
                # Refresh user data from API to get latest experience level and progress
                try:
                    updated_user = st.session_state.api_client.get_user_by_id(user.get('user_id'))
                    if updated_user and "error" not in updated_user:
                        # Update session state with fresh data
                        st.session_state.current_user.update(updated_user)
                        user = st.session_state.current_user
                    
                    # Get analytics for progress
                    analytics = st.session_state.api_client.get_progress_analytics(user.get('user_id'))
                    if analytics and 'overall_completion' in analytics:
                        progress = analytics['overall_completion']
                    else:
                        progress = 0.0
                    
                    st.markdown(f"Experience: {user.get('experience_level', 'Unknown').title()}")
                    st.markdown(f"Progress: {progress:.1f}%")
                except Exception:
                    st.markdown(f"Experience: {user.get('experience_level', 'Unknown').title()}")
                    st.markdown(f"Progress: 0.0%")
                
                if st.button("🚪 Logout", use_container_width=True):
                    st.session_state.current_user = None
                    st.session_state.current_session_id = None
                    st.session_state.page = "welcome"
                    st.rerun()
        
        st.markdown("---")
        
        # Navigation menu
        if st.session_state.current_user:
            # Check if onboarding is completed
            if not st.session_state.current_user.get("onboarding_completed", False):
                st.markdown("### Complete Setup")
                if st.button("📋 Continue Onboarding", use_container_width=True):
                    st.session_state.page = "onboarding"
                    st.rerun()
            else:
                st.markdown("### Navigation")
                
                if st.button("📊 Dashboard", use_container_width=True):
                    st.session_state.page = "dashboard"
                    st.rerun()
                
                if st.button("💬 Chat with Agent", use_container_width=True):
                    st.session_state.page = "chat"
                    st.rerun()
                
                if st.button("📚 Learning Plan", use_container_width=True):
                    st.session_state.page = "learning_plan"
                    st.rerun()
                
                if st.button("👤 Profile Settings", use_container_width=True):
                    st.session_state.page = "profile"
                    st.rerun()
        
        else:
            st.markdown("### Get Started")
            if st.button("🔑 Login", use_container_width=True):
                st.session_state.page = "login"
                st.rerun()
            
            if st.button("📝 Register", use_container_width=True):
                st.session_state.page = "register"
                st.rerun()
        
        # API status
        st.markdown("---")
        st.markdown("### System Status")
        check_api_status()

def render_welcome_page():
    """Render the welcome page."""
    st.markdown('<h1 class="main-header">🎯 TOGAF Learning Agent</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        ### Welcome to Your Personal TOGAF Tutor! 
        
        Master enterprise architecture with AI-powered personalized learning:
        
        🎓 **Personalized Learning**
        - Adaptive content based on your experience level
        - Customized study plans and progress tracking
        
        📚 **Comprehensive Coverage**
        - TOGAF Foundation and Practitioner levels
        - Interactive conversations and explanations
        
        🎯 **Exam Preparation**
        - Practice questions and knowledge gap analysis
        - Certification readiness assessment
        
        📊 **Progress Tracking**
        - Detailed analytics and learning insights
        - Achievement tracking and recommendations
        
        ---
        
        **Ready to start your TOGAF journey?**
        """)
        
        col_login, col_register = st.columns(2)
        
        with col_login:
            if st.button("🔑 Login", use_container_width=True, type="secondary"):
                st.session_state.page = "login"
                st.rerun()
        
        with col_register:
            if st.button("📝 Get Started", use_container_width=True, type="primary"):
                st.session_state.page = "register"
                st.rerun()

def render_login_page():
    """Render the login page."""
    st.markdown('<h1 class="main-header">🔑 Login</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            st.markdown("### Enter Your Credentials")
            
            username = st.text_input("Username", placeholder="Enter your username")
            
            col_submit, col_back = st.columns(2)
            
            with col_submit:
                submitted = st.form_submit_button("Login", use_container_width=True, type="primary")
            
            with col_back:
                back_clicked = st.form_submit_button("Back", use_container_width=True)
            
            if back_clicked:
                st.session_state.page = "welcome"
                st.rerun()
            
            if submitted and username:
                # Try to get user by username
                user_data = st.session_state.api_client.get_user_by_username(username)
                
                if user_data and "error" not in user_data:
                    st.session_state.current_user = user_data
                    
                    # Check if onboarding is completed
                    if user_data.get("onboarding_completed", False):
                        st.session_state.page = "dashboard"
                    else:
                        st.session_state.page = "onboarding"
                    
                    st.success(f"Welcome back, {username}!")
                    st.rerun()
                else:
                    st.error("User not found. Please check your username or register first.")
            elif submitted:
                st.error("Please enter a username")

def render_register_page():
    """Render the registration page."""
    st.markdown('<h1 class="main-header">📝 Create Account</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("register_form"):
            st.markdown("### Join the TOGAF Learning Community")
            
            username = st.text_input(
                "Username", 
                placeholder="Choose a unique username",
                help="This will be your identifier in the system"
            )
            
            email = st.text_input(
                "Email (Optional)", 
                placeholder="your.email@example.com",
                help="For progress updates and reminders"
            )
            
            col_submit, col_back = st.columns(2)
            
            with col_submit:
                submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")
            
            with col_back:
                back_clicked = st.form_submit_button("Back", use_container_width=True)
            
            if back_clicked:
                st.session_state.page = "welcome"
                st.rerun()
            
            if submitted and username:
                # Create new user
                user_data = st.session_state.api_client.create_user(username, email or None)
                
                if user_data and "error" not in user_data:
                    st.session_state.current_user = user_data
                    st.session_state.page = "onboarding"
                    st.success(f"Account created successfully! Welcome, {username}!")
                    st.rerun()
                else:
                    error_msg = user_data.get("detail", "Failed to create account") if user_data else "Failed to create account"
                    st.error(error_msg)
            elif submitted:
                st.error("Please enter a username")

def render_profile_page():
    """Render the user profile management page."""
    if not st.session_state.current_user:
        st.error("Please login first")
        return
    
    st.markdown('<h1 class="main-header">👤 Profile Settings</h1>', unsafe_allow_html=True)
    
    user = st.session_state.current_user
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Profile Information
        st.markdown("### Profile Information")
        
        with st.form("profile_form"):
            current_email = user.get("email", "")
            email = st.text_input("Email", value=current_email)
            
            current_cert = user.get("target_certification", "")
            target_certification = st.selectbox(
                "Target Certification",
                ["foundation", "practitioner"],
                index=0 if current_cert == "foundation" else (1 if current_cert == "practitioner" else 0)
            )
            
            exam_prep = st.checkbox(
                "Exam Preparation Mode",
                value=user.get("exam_preparation_mode", False),
                help="Focus on certification exam preparation"
            )
            
            if st.form_submit_button("Update Profile", type="primary"):
                # Update user profile
                update_data = {
                    "email": email if email != current_email else None,
                    "target_certification": target_certification,
                    "exam_preparation_mode": exam_prep
                }
                
                # Remove None values
                update_data = {k: v for k, v in update_data.items() if v is not None}
                
                if update_data:
                    result = st.session_state.api_client.update_user(user["user_id"], update_data)
                    
                    if result and "error" not in result:
                        st.success("Profile updated successfully!")
                        # Update session state
                        st.session_state.current_user.update(result)
                        st.rerun()
                    else:
                        st.error("Failed to update profile")
                else:
                    st.info("No changes to save")
        
        # User Statistics
        st.markdown("### Learning Statistics")
        stats = st.session_state.api_client.get_user_statistics(user["user_id"])
        
        if stats:
            col_stats1, col_stats2 = st.columns(2)
            
            with col_stats1:
                st.metric("Overall Progress", f"{stats.get('profile', {}).get('overall_proficiency', 0):.1%}")
                st.metric("Study Sessions", stats.get('activity', {}).get('total_sessions', 0))
            
            with col_stats2:
                st.metric("Topics Studied", stats.get('progress', {}).get('topics_studied', 0))
                st.metric("Current Streak", f"{stats.get('activity', {}).get('current_streak', 0)} days")
    
    with col2:
        # Quick Actions
        st.markdown("### Quick Actions")
        
        if st.button("🔄 Restart Onboarding", use_container_width=True):
            st.session_state.page = "onboarding"
            st.rerun()
        
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
        
        if st.button("📚 Manage Learning Plans", use_container_width=True):
            st.session_state.page = "learning_plan"
            st.rerun()
        
        st.markdown("### 🔄 Reset Options")
        
        # Refresh Current Plan (for empty plans like "prady")
        if st.button("🔧 Refresh Current Plan", use_container_width=True, help="Add latest topics to current plan"):
            with st.spinner("Refreshing your current learning plan..."):
                result = st.session_state.api_client.reset_learning_progress(user["user_id"], "refresh_current_plan")
                if result and "error" not in result:
                    st.success("✅ Learning plan refreshed with latest topics!")
                    st.rerun()
                else:
                    st.error("❌ Failed to refresh learning plan")
        
        # Reset Progress Only
        if st.button("🔄 Reset Learning Progress", use_container_width=True, help="Reset progress but keep settings"):
            with st.spinner("Resetting your learning progress..."):
                result = st.session_state.api_client.reset_learning_progress(user["user_id"], "progress_only")
                if result and "error" not in result:
                    st.success("✅ Learning progress reset successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to reset learning progress")
        
        # Reset Learning Plans
        # Initialize confirmation state for learning plans
        if "show_plans_reset_confirm" not in st.session_state:
            st.session_state.show_plans_reset_confirm = False
        
        if not st.session_state.show_plans_reset_confirm:
            if st.button("🗂️ Reset Learning Plans", use_container_width=True, help="Clear all plans, keep profile"):
                st.session_state.show_plans_reset_confirm = True
                st.rerun()
        else:
            st.warning("⚠️ This will clear all your learning plans but keep your profile settings.")
            
            col_confirm, col_cancel = st.columns(2)
            
            with col_confirm:
                if st.button("⚠️ Confirm Reset Plans", use_container_width=True, type="primary"):
                    with st.spinner("Resetting all learning plans..."):
                        result = st.session_state.api_client.reset_learning_progress(user["user_id"], "learning_plans")
                        if result and "error" not in result:
                            st.success("✅ Learning plans reset successfully!")
                            st.session_state.show_plans_reset_confirm = False
                            st.rerun()
                        else:
                            st.error("❌ Failed to reset learning plans")
                            st.session_state.show_plans_reset_confirm = False
            
            with col_cancel:
                if st.button("❌ Cancel Plans Reset", use_container_width=True):
                    st.session_state.show_plans_reset_confirm = False
                    st.rerun()
        
        # Full Reset
        with st.expander("🚨 Advanced Reset Options"):
            st.warning("⚠️ **DANGER ZONE** - These actions cannot be undone!")
            
            # Initialize confirmation state
            if "show_complete_reset_confirm" not in st.session_state:
                st.session_state.show_complete_reset_confirm = False
            
            if not st.session_state.show_complete_reset_confirm:
                if st.button("🔥 Complete Reset", use_container_width=True, help="Reset everything, restart onboarding"):
                    st.session_state.show_complete_reset_confirm = True
                    st.rerun()
            else:
                st.warning("⚠️ This will reset your entire learning profile!")
                st.markdown("**This action will:**")
                st.markdown("- Clear all learning progress and plans")
                st.markdown("- Reset experience level and proficiency scores")
                st.markdown("- Force you to complete onboarding again")
                st.markdown("- Keep only your username and email")
                
                col_confirm, col_cancel = st.columns(2)
                
                with col_confirm:
                    if st.button("💥 CONFIRM COMPLETE RESET", use_container_width=True, type="primary"):
                        with st.spinner("Performing complete reset..."):
                            result = st.session_state.api_client.reset_learning_progress(user["user_id"], "full_reset")
                            if result and "error" not in result:
                                st.success("✅ Complete reset successful! Please log out and log back in.")
                                st.balloons()
                                st.session_state.show_complete_reset_confirm = False
                            else:
                                st.error("❌ Failed to perform complete reset")
                                st.session_state.show_complete_reset_confirm = False
                
                with col_cancel:
                    if st.button("❌ Cancel", use_container_width=True):
                        st.session_state.show_complete_reset_confirm = False
                        st.rerun()
        
        # Account Information
        st.markdown("### Account Information")
        st.markdown(f"**Username:** {user.get('username', 'Unknown')}")
        st.markdown(f"**Experience Level:** {user.get('experience_level', 'Unknown').title()}")
        st.markdown(f"**Member Since:** {user.get('created_at', 'Unknown')[:10]}")
        st.markdown(f"**Last Active:** {user.get('last_active', 'Unknown')[:10]}")

def check_api_status():
    """Check and display API connection status."""
    try:
        health = st.session_state.api_client.get_health()
        
        if health.get("status") == "healthy":
            st.success("🟢 API Connected")
        elif health.get("status") == "degraded":
            st.warning("🟡 API Degraded")
        else:
            st.error("🔴 API Issues")
    except:
        st.error("🔴 API Offline")

if __name__ == "__main__":
    main()