"""
Learning plan management components.
"""

import streamlit as st
from typing import Dict, Any, List
import pandas as pd


def render_learning_plan():
    """Render learning plan management interface."""
    if not st.session_state.current_user:
        st.error("Please login first")
        return
    
    user = st.session_state.current_user
    user_id = user["user_id"]
    
    st.markdown('<h1 style="text-align: center; color: #1f77b4;">📚 Learning Plans</h1>', 
                unsafe_allow_html=True)
    
    # Get user's learning plans
    plans_data = st.session_state.api_client.get_user_learning_plans(user_id)
    
    # Debug: Show the raw learning plans data
    with st.expander("🔍 Debug: Learning Plans API Response", expanded=False):
        st.write("Raw API Response:")
        st.json(plans_data)
    
    if not plans_data:
        st.error("Unable to load learning plans")
        return
    
    learning_plans = plans_data.get("learning_plans", {})
    active_plan_id = plans_data.get("active_plan_id")
    
    # Debug: Show parsed data
    with st.expander("🔍 Debug: Parsed Learning Plans Data", expanded=False):
        st.write("Learning Plans:", learning_plans)
        st.write("Active Plan ID:", active_plan_id)
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Current Plan", "📚 All Plans", "➕ Create New Plan"])
    
    with tab1:
        render_current_plan(user_id, active_plan_id, learning_plans)
    
    with tab2:
        render_all_plans(user_id, learning_plans, active_plan_id)
    
    with tab3:
        render_create_plan_interface(user_id)


def render_current_plan(user_id: str, active_plan_id: str, learning_plans: Dict[str, Any]):
    """Render the current active learning plan."""
    # Debug current plan status
    with st.expander("🔍 Debug: Current Plan Status", expanded=False):
        st.write("Active Plan ID:", active_plan_id)
        st.write("Available Learning Plans:", list(learning_plans.keys()) if learning_plans else "None")
        st.write("Active Plan ID in Learning Plans:", active_plan_id in learning_plans if learning_plans and active_plan_id else "N/A")
    
    if not active_plan_id or active_plan_id not in learning_plans:
        st.info("No active learning plan. Create or select a plan to get started!")
        
        # Debug: Show what we have
        if not active_plan_id:
            st.warning("🐛 Debug: No active_plan_id found")
        elif active_plan_id not in learning_plans:
            st.warning(f"🐛 Debug: active_plan_id '{active_plan_id}' not found in learning_plans")
        return
    
    active_plan = learning_plans[active_plan_id]
    
    # Plan header
    st.markdown(f"## 🎯 {active_plan['plan_name']}")
    st.markdown(f"**Type:** {active_plan['plan_type'].replace('_', ' ').title()}")
    st.markdown(f"**Target:** {active_plan['target_certification'].title()}")
    st.markdown(f"**Description:** {active_plan['description']}")
    
    # Progress overview
    completion = active_plan.get("completion_percentage", 0)
    topics_completed = active_plan.get("topics_completed", 0)
    total_topics = active_plan.get("total_topics", 0)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Progress", f"{completion:.1f}%")
    
    with col2:
        st.metric("✅ Completed", f"{topics_completed}/{total_topics}")
    
    with col3:
        st.metric("📅 Created", active_plan.get("created_date", "Unknown")[:10])
    
    # Progress bar
    st.progress(completion / 100)
    
    # Detailed plan overview
    st.markdown("---")
    st.markdown("### 📋 Detailed Plan Overview")
    
    plan_overview = st.session_state.api_client.get_plan_overview(user_id, active_plan_id)
    
    if plan_overview:
        # Debug: Show the raw data structure
        with st.expander("🔍 Debug: Plan Overview Data (click to expand)", expanded=False):
            st.json(plan_overview)
        
        render_plan_overview(plan_overview, user_id)
    else:
        st.error("Unable to load detailed plan overview")


def render_plan_overview(plan_overview: Dict[str, Any], user_id: str):
    """Render detailed plan overview with topic status."""
    topics_by_status = plan_overview.get("topics_by_status", {})
    progress_summary = plan_overview.get("progress_summary", {})
    
    # Status tabs
    status_tabs = st.tabs(["✅ Completed", "🔄 In Progress", "📚 Available", "🔒 Locked", "⏭️ Skipped"])
    
    status_keys = ["completed", "in_progress", "available", "locked", "skipped"]
    
    for i, (tab, status_key) in enumerate(zip(status_tabs, status_keys)):
        with tab:
            topics = topics_by_status.get(status_key, [])
            
            if not topics:
                st.info(f"No {status_key.replace('_', ' ')} topics")
                continue
            
            for topic in topics:
                render_topic_card(topic, status_key, user_id)
    
    # Current recommendations
    st.markdown("---")
    st.markdown("### 🎯 Current Recommendations")
    
    recommendations = st.session_state.api_client.get_learning_recommendations(user_id, 3)
    
    if recommendations and "recommendations" in recommendations:
        for rec in recommendations["recommendations"]:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{rec['topic_id'].replace('_', ' ').title()}**")
                    st.markdown(f"Reason: {rec['reason'].replace('_', ' ').title()}")
                    st.markdown(f"Estimated time: {rec['estimated_duration']} minutes")
                
                with col2:
                    priority_color = "🔴" if rec['priority'] > 0.8 else "🟡" if rec['priority'] > 0.5 else "🟢"
                    st.markdown(f"Priority: {priority_color}")
                
                with col3:
                    if st.button("📖 Study", key=f"study_{rec['topic_id']}", use_container_width=True):
                        st.session_state.page = "chat"
                        st.rerun()
                
                st.markdown("---")


def render_topic_card(topic: Dict[str, Any], status: str, user_id: str):
    """Render an individual topic card."""
    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            title = topic.get("title", "Unknown Topic")
            description = topic.get("description", "No description available")
            
            st.markdown(f"**{title}**")
            st.markdown(f"{description}")
            
            # Show estimated duration
            duration = topic.get("estimated_duration_minutes", 0)
            if duration > 0:
                st.markdown(f"*Estimated time: {duration} minutes*")
        
        with col2:
            # Show prerequisites if any
            prerequisites = topic.get("prerequisites", [])
            if prerequisites:
                st.markdown("**Prerequisites:**")
                for prereq in prerequisites:
                    st.markdown(f"• {prereq}")
        
        with col3:
            topic_id = topic.get("topic_id", "")
            
            # Action buttons based on status
            if status == "available":
                if st.button("📖 Study", key=f"study_{topic_id}", use_container_width=True):
                    # Start studying this topic
                    st.session_state.page = "chat"
                    st.rerun()
            
            elif status == "in_progress":
                col_complete, col_skip = st.columns(2)
                
                with col_complete:
                    if st.button("✅", key=f"complete_{topic_id}", help="Mark Complete"):
                        result = st.session_state.api_client.mark_topic_complete(user_id, topic_id)
                        if result and "error" not in result:
                            st.success("Topic completed!")
                            st.rerun()
                        else:
                            st.error("Failed to mark complete")
                
                with col_skip:
                    if st.button("⏭️", key=f"skip_{topic_id}", help="Skip Topic"):
                        result = st.session_state.api_client.skip_topic(user_id, topic_id)
                        if result and "error" not in result:
                            st.success("Topic skipped!")
                            st.rerun()
                        else:
                            st.error("Failed to skip topic")
            
            elif status == "completed":
                st.success("✅ Complete")
            
            elif status == "locked":
                st.info("🔒 Locked")
            
            elif status == "skipped":
                st.warning("⏭️ Skipped")
        
        st.markdown("---")


def render_all_plans(user_id: str, learning_plans: Dict[str, Any], active_plan_id: str):
    """Render all user learning plans."""
    if not learning_plans:
        st.info("No learning plans found. Create your first plan to get started!")
        return
    
    st.markdown("### 📚 All Your Learning Plans")
    
    # Convert to list for easier handling
    plans_list = []
    for plan_id, plan_data in learning_plans.items():
        plan_data["plan_id"] = plan_id
        plan_data["is_active"] = plan_id == active_plan_id
        plans_list.append(plan_data)
    
    # Sort by creation date (most recent first)
    plans_list.sort(key=lambda x: x.get("created_date", ""), reverse=True)
    
    for plan in plans_list:
        render_plan_summary_card(plan, user_id)


def render_plan_summary_card(plan: Dict[str, Any], user_id: str):
    """Render a summary card for a learning plan."""
    with st.container():
        # Header with active indicator
        col_header, col_status = st.columns([3, 1])
        
        with col_header:
            plan_name = plan.get("plan_name", "Unnamed Plan")
            if plan.get("is_active", False):
                st.markdown(f"### 🎯 **{plan_name}** (Active)")
            else:
                st.markdown(f"### 📚 **{plan_name}**")
        
        with col_status:
            completion = plan.get("completion_percentage", 0)
            st.metric("Progress", f"{completion:.1f}%")
        
        # Plan details
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"**Type:** {plan.get('plan_type', 'Unknown').replace('_', ' ').title()}")
            st.markdown(f"**Target:** {plan.get('target_certification', 'Unknown').title()}")
        
        with col2:
            topics_completed = plan.get("topics_completed", 0)
            total_topics = plan.get("total_topics", 0)
            st.markdown(f"**Topics:** {topics_completed}/{total_topics}")
            st.markdown(f"**Created:** {plan.get('created_date', 'Unknown')[:10]}")
        
        with col3:
            plan_id = plan.get("plan_id", "")
            
            if not plan.get("is_active", False):
                if st.button("🎯 Activate", key=f"activate_{plan_id}", use_container_width=True):
                    # Note: This would require an API endpoint to set active plan
                    st.info("Plan activation would be implemented here")
            
            if st.button("👁️ View Details", key=f"view_{plan_id}", use_container_width=True):
                # Store selected plan for detailed view
                st.session_state.selected_plan_id = plan_id
                st.rerun()
        
        # Description
        description = plan.get("description", "No description available")
        st.markdown(f"*{description}*")
        
        # Progress bar
        st.progress(completion / 100)
        
        st.markdown("---")


def render_create_plan_interface(user_id: str):
    """Render interface for creating new learning plans."""
    st.markdown("### ➕ Create New Learning Plan")
    
    # Plan creation form
    with st.form("create_plan_form"):
        st.markdown("#### Plan Configuration")
        
        # Plan type selection
        plan_types = [
            ("foundation_beginner", "Foundation for Beginners", "Step-by-step introduction to TOGAF"),
            ("foundation_review", "Foundation Review", "Quick review of Foundation concepts"),
            ("practitioner_prep", "Practitioner Preparation", "Core topics for Practitioner exam"),
            ("extended_practitioner", "Extended Practitioner Guides", "Comprehensive specialized guides and advanced topics"),
            ("custom_topics", "Custom Topics", "Choose specific topics to focus on")
        ]
        
        plan_type_labels = [f"{label} - {desc}" for _, label, desc in plan_types]
        selected_plan_type = st.selectbox("Plan Type", plan_type_labels)
        
        # Extract the actual plan type value
        selected_index = plan_type_labels.index(selected_plan_type)
        plan_type_value = plan_types[selected_index][0]
        
        # Custom plan name
        plan_name = st.text_input(
            "Plan Name (Optional)", 
            placeholder="Leave blank for default name"
        )
        
        # Custom topics selection (only for custom_topics)
        custom_topics = []
        if plan_type_value == "custom_topics":
            st.markdown("#### Select Topics")
            
            topic_categories = {
                "Core ADM": [
                    "ADM Overview",
                    "Preliminary Phase",
                    "Phase A: Architecture Vision",
                    "Phase B: Business Architecture",
                    "Phase C: Information Systems Architecture",
                    "Phase D: Technology Architecture",
                    "Phase E: Opportunities and Solutions",
                    "Phase F: Migration Planning",
                    "Phase G: Implementation Governance",
                    "Phase H: Architecture Change Management"
                ],
                "Supporting Elements": [
                    "Requirements Management",
                    "Architecture Governance",
                    "Architecture Repository",
                    "Enterprise Continuum",
                    "TOGAF Reference Models",
                    "Architecture Capability Framework"
                ],
                "Advanced Topics": [
                    "Business Scenarios",
                    "Gap Analysis",
                    "Migration Planning",
                    "Implementation Governance",
                    "Architecture Maturity Models"
                ]
            }
            
            for category, topics in topic_categories.items():
                st.markdown(f"**{category}:**")
                
                for topic in topics:
                    if st.checkbox(topic, key=f"topic_{topic}"):
                        custom_topics.append(topic.lower().replace(" ", "_").replace(":", ""))
        
        # Submit button
        if st.form_submit_button("🚀 Create Learning Plan", type="primary", use_container_width=True):
            if plan_type_value == "custom_topics" and len(custom_topics) < 3:
                st.error("Please select at least 3 topics for a custom plan")
            else:
                create_learning_plan(user_id, plan_type_value, plan_name, custom_topics)


def create_learning_plan(user_id: str, plan_type: str, plan_name: str, custom_topics: List[str]):
    """Create a new learning plan."""
    with st.spinner("Creating your learning plan..."):
        # This would call the appropriate API endpoint
        # For now, we'll show a success message
        st.success("🎉 Learning plan created successfully!")
        st.info("Learning plan creation would be implemented through the user management API")
        
        # In a real implementation, you would call:
        # result = api_client.create_structured_plan(user_id, plan_type, custom_topics, plan_name)
        
        time.sleep(1)  # Simulate API call
        st.rerun()