"""
Onboarding flow components for Streamlit UI.
"""

import streamlit as st
from typing import Dict, Any, List


def render_onboarding_flow():
    """Render the complete onboarding flow."""
    if not st.session_state.current_user:
        st.error("Please login first")
        return
    
    user_id = st.session_state.current_user["user_id"]
    
    # Check if onboarding is already started
    if "onboarding_state" not in st.session_state:
        # Start onboarding
        result = st.session_state.api_client.start_onboarding(user_id)
        
        if result and "error" not in result:
            st.session_state.onboarding_state = result
        else:
            st.error(f"Failed to start onboarding: {result.get('detail', 'Unknown error')}")
            return
    
    onboarding_state = st.session_state.onboarding_state
    
    # Render current step
    current_step = onboarding_state.get("step", "welcome")
    
    if current_step == "welcome":
        render_welcome_step()
    elif current_step == "experience_assessment":
        render_assessment_step()
    elif current_step == "learning_preferences":
        render_preferences_step()
    elif current_step == "goal_setting":
        render_goals_step()
    elif current_step == "plan_selection":
        render_plan_selection_step()
    elif current_step == "session_preferences":
        render_session_preferences_step()
    elif current_step == "completion":
        render_completion_step()
    else:
        st.error(f"Unknown onboarding step: {current_step}")


def render_welcome_step():
    """Render the welcome step."""
    st.markdown('<h1 style="text-align: center; color: #1f77b4;">🎯 Welcome to Your TOGAF Journey!</h1>', 
                unsafe_allow_html=True)
    
    onboarding_state = st.session_state.onboarding_state
    
    # Display welcome content
    content = onboarding_state.get("content", [])
    for line in content:
        if line.strip():
            st.markdown(f"• {line}")
    
    st.markdown("---")
    
    # Question and options
    question = onboarding_state.get("question", "Are you ready to get started?")
    st.markdown(f"### {question}")
    
    options = onboarding_state.get("options", ["Yes, let's begin!", "I need more information first"])
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(options[0], use_container_width=True, type="primary"):
            process_onboarding_response("welcome", {"response": options[0]})
    
    if len(options) > 1:
        with col2:
            if st.button(options[1], use_container_width=True):
                process_onboarding_response("welcome", {"response": options[1]})


def render_assessment_step():
    """Render the experience assessment step."""
    st.markdown('<h1 style="text-align: center; color: #1f77b4;">🧠 Knowledge Assessment</h1>', 
                unsafe_allow_html=True)
    
    onboarding_state = st.session_state.onboarding_state
    
    # Display instructions
    content = onboarding_state.get("content", [])
    for line in content:
        if line.strip():
            st.markdown(line)
    
    st.markdown("---")
    
    # Assessment questions
    assessment = onboarding_state.get("assessment", {})
    questions = assessment.get("questions", [])
    
    if not questions:
        st.error("No assessment questions available")
        return
    
    # Assessment form
    with st.form("assessment_form"):
        st.markdown("### Assessment Questions")
        
        responses = {}
        
        for i, question in enumerate(questions):
            st.markdown(f"**Question {i+1}:** {question['question_text']}")
            
            options = question.get("options", [])
            if not options:
                continue
            
            # Add "I don't know" option if not present
            if "I don't know" not in options:
                options.append("I don't know")
            
            response = st.radio(
                f"Select your answer:",
                options,
                index=None,  # No default selection
                key=f"q_{question['question_id']}",
                label_visibility="collapsed"
            )
            
            responses[question["question_id"]] = response
            st.markdown("---")
        
        if st.form_submit_button("Continue", type="primary", use_container_width=True):
            if len(responses) == len(questions):
                process_onboarding_response("experience_assessment", {"responses": responses})
            else:
                st.error("Please answer all questions")


def render_preferences_step():
    """Render the learning preferences step."""
    st.markdown('<h1 style="text-align: center; color: #1f77b4;">🎨 Learning Preferences</h1>', 
                unsafe_allow_html=True)
    
    onboarding_state = st.session_state.onboarding_state
    
    # Display feedback and experience level
    feedback = onboarding_state.get("feedback", "")
    if feedback:
        st.success(feedback)
    
    experience_level = onboarding_state.get("experience_level", "")
    if experience_level:
        st.info(experience_level)
    
    st.markdown("---")
    
    # Learning preferences form
    with st.form("preferences_form"):
        st.markdown("### How do you prefer to learn?")
        
        questions = onboarding_state.get("questions", [])
        preferences = {}
        
        for question in questions:
            st.markdown(f"**{question['question']}**")
            
            if question["type"] == "single_choice":
                options = [opt["label"] for opt in question["options"]]
                values = [opt["value"] for opt in question["options"]]
                
                # Show descriptions
                for opt in question["options"]:
                    st.markdown(f"• **{opt['label']}**: {opt.get('description', '')}")
                
                selected = st.radio(
                    "Choose one:",
                    options,
                    key=f"pref_{question['id']}",
                    label_visibility="collapsed"
                )
                
                # Map back to value
                selected_idx = options.index(selected) if selected in options else 0
                preferences[question["id"]] = values[selected_idx]
            
            st.markdown("---")
        
        if st.form_submit_button("Continue", type="primary", use_container_width=True):
            process_onboarding_response("learning_preferences", {"preferences": preferences})


def render_goals_step():
    """Render the goal setting step."""
    st.markdown('<h1 style="text-align: center; color: #1f77b4;">🎯 Learning Goals</h1>', 
                unsafe_allow_html=True)
    
    onboarding_state = st.session_state.onboarding_state
    
    # Display content
    content = onboarding_state.get("content", [])
    for line in content:
        if line.strip():
            st.markdown(line)
    
    st.markdown("---")
    
    # Goals form
    with st.form("goals_form"):
        st.markdown("### Set Your Learning Goals")
        
        questions = onboarding_state.get("questions", [])
        goals = {}
        
        for question in questions:
            st.markdown(f"**{question['question']}**")
            
            if question["type"] == "single_choice":
                options = [opt["label"] for opt in question["options"]]
                values = [opt["value"] for opt in question["options"]]
                
                # Show descriptions
                for opt in question["options"]:
                    st.markdown(f"• **{opt['label']}**: {opt.get('description', '')}")
                
                selected = st.radio(
                    "Choose one:",
                    options,
                    key=f"goal_{question['id']}",
                    label_visibility="collapsed"
                )
                
                selected_idx = options.index(selected) if selected in options else 0
                goals[question["id"]] = values[selected_idx]
            
            elif question["type"] == "yes_no":
                answer = st.radio(
                    question["question"],
                    ["Yes", "No"],
                    key=f"goal_{question['id']}",
                    label_visibility="collapsed"
                )
                goals[question["id"]] = answer == "Yes"
                
                # Handle follow-up questions
                if answer == "Yes" and "follow_up" in question:
                    follow_up = question["follow_up"]["yes"]
                    st.markdown(f"**{follow_up['question']}**")
                    
                    follow_options = [opt["label"] for opt in follow_up["options"]]
                    follow_values = [opt["value"] for opt in follow_up["options"]]
                    
                    follow_selected = st.radio(
                        "Select timeline:",
                        follow_options,
                        key=f"goal_{question['id']}_followup",
                        label_visibility="collapsed"
                    )
                    
                    follow_idx = follow_options.index(follow_selected) if follow_selected in follow_options else 0
                    goals[f"{question['id']}_timeline"] = follow_values[follow_idx]
            
            elif question["type"] == "multiple_choice":
                st.markdown("Select all that apply:")
                selected_areas = []
                
                for opt in question["options"]:
                    if st.checkbox(opt["label"], key=f"goal_{question['id']}_{opt['value']}"):
                        selected_areas.append(opt["value"])
                
                goals[question["id"]] = selected_areas
            
            st.markdown("---")
        
        if st.form_submit_button("Continue", type="primary", use_container_width=True):
            process_onboarding_response("goal_setting", {"goals": goals})


def render_plan_selection_step():
    """Render the plan selection step."""
    st.markdown('<h1 style="text-align: center; color: #1f77b4;">📚 Choose Your Learning Plan</h1>', 
                unsafe_allow_html=True)
    
    onboarding_state = st.session_state.onboarding_state
    
    # Display content
    content = onboarding_state.get("content", [])
    for line in content:
        if line.strip():
            st.markdown(line)
    
    st.markdown("---")
    
    # Plan selection
    recommended_plans = onboarding_state.get("recommended_plans", [])
    
    if not recommended_plans:
        st.error("No learning plans available")
        return
    
    st.markdown("### Available Learning Plans")
    
    selected_plan = None
    custom_topics = []
    
    for i, plan in enumerate(recommended_plans):
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if plan.get("recommended", False):
                    st.markdown(f"**🌟 {plan['name']}** (Recommended)")
                else:
                    st.markdown(f"**{plan['name']}**")
                
                st.markdown(plan.get("description", ""))
                st.markdown(f"*Estimated Duration: {plan.get('duration', 'Variable')}*")
            
            with col2:
                if st.button(f"Select", key=f"plan_{i}", use_container_width=True,
                           type="primary" if plan.get("recommended", False) else "secondary"):
                    selected_plan = plan["type"]
            
            st.markdown("---")
    
    # Handle custom topics selection
    if selected_plan == "custom_topics":
        st.markdown("### Select Custom Topics")
        st.markdown("Choose the TOGAF topics you want to focus on:")
        
        topic_options = [
            "ADM Overview",
            "Preliminary Phase",
            "Phase A: Architecture Vision",
            "Phase B: Business Architecture",
            "Phase C: Information Systems Architecture",
            "Phase D: Technology Architecture",
            "Phase E: Opportunities and Solutions",
            "Phase F: Migration Planning",
            "Phase G: Implementation Governance",
            "Phase H: Architecture Change Management",
            "Requirements Management",
            "Architecture Governance",
            "Architecture Repository",
            "Enterprise Continuum",
            "TOGAF Reference Models"
        ]
        
        custom_topics = st.multiselect(
            "Select topics (choose at least 3):",
            topic_options,
            help="Select the topics most relevant to your learning goals"
        )
        
        if custom_topics and len(custom_topics) >= 3:
            if st.button("Continue with Custom Topics", type="primary", use_container_width=True):
                response_data = {
                    "selected_plan": selected_plan,
                    "custom_topics": [topic.lower().replace(" ", "_").replace(":", "") for topic in custom_topics]
                }
                process_onboarding_response("plan_selection", response_data)
        elif custom_topics:
            st.warning("Please select at least 3 topics for your custom plan")
    
    elif selected_plan:
        response_data = {"selected_plan": selected_plan}
        process_onboarding_response("plan_selection", response_data)


def render_session_preferences_step():
    """Render the session preferences step."""
    st.markdown('<h1 style="text-align: center; color: #1f77b4;">⚙️ Session Preferences</h1>', 
                unsafe_allow_html=True)
    
    onboarding_state = st.session_state.onboarding_state
    
    # Display content
    content = onboarding_state.get("content", [])
    for line in content:
        if line.strip():
            st.markdown(line)
    
    st.markdown("---")
    
    # Session preferences form
    with st.form("session_preferences_form"):
        st.markdown("### Customize Your Learning Sessions")
        
        questions = onboarding_state.get("questions", [])
        session_prefs = {}
        
        for question in questions:
            st.markdown(f"**{question['question']}**")
            
            options = [opt["label"] for opt in question["options"]]
            values = [opt["value"] for opt in question["options"]]
            
            # Show descriptions if available
            for opt in question["options"]:
                if "description" in opt:
                    st.markdown(f"• **{opt['label']}**: {opt['description']}")
                else:
                    st.markdown(f"• {opt['label']}")
            
            selected = st.radio(
                "Choose one:",
                options,
                key=f"session_{question['id']}",
                label_visibility="collapsed"
            )
            
            selected_idx = options.index(selected) if selected in options else 0
            session_prefs[question["id"]] = values[selected_idx]
            
            st.markdown("---")
        
        if st.form_submit_button("Complete Setup", type="primary", use_container_width=True):
            process_onboarding_response("session_preferences", {"session_preferences": session_prefs})


def render_completion_step():
    """Render the completion step."""
    st.markdown('<h1 style="text-align: center; color: #28a745;">🎉 Setup Complete!</h1>', 
                unsafe_allow_html=True)
    
    onboarding_state = st.session_state.onboarding_state
    
    # Display completion content
    content = onboarding_state.get("content", [])
    for line in content:
        if line.strip():
            if line.startswith("**") and line.endswith("**"):
                st.markdown(f"### {line[2:-2]}")
            else:
                st.markdown(line)
    
    st.markdown("---")
    
    # Next actions
    next_actions = onboarding_state.get("next_actions", [])
    
    if next_actions:
        st.markdown("### What would you like to do first?")
        
        cols = st.columns(len(next_actions))
        
        for i, action in enumerate(next_actions):
            with cols[i]:
                if st.button(action["label"], use_container_width=True, type="primary" if i == 0 else "secondary"):
                    # Handle action
                    if action["action"] == "start_session":
                        st.session_state.page = "chat"
                    elif action["action"] == "view_plan":
                        st.session_state.page = "learning_plan"
                    elif action["action"] == "ask_question":
                        st.session_state.page = "chat"
                    
                    # Mark onboarding as completed and refresh user data from API
                    st.session_state.current_user["onboarding_completed"] = True
                    
                    # Refresh user profile from API to get updated experience level and other changes
                    updated_user = st.session_state.api_client.get_user_by_id(st.session_state.current_user["user_id"])
                    if updated_user and "error" not in updated_user:
                        st.session_state.current_user.update(updated_user)
                    
                    # Clear onboarding state
                    if "onboarding_state" in st.session_state:
                        del st.session_state.onboarding_state
                    
                    st.rerun()
    
    # Manual completion option
    st.markdown("---")
    if st.button("Go to Dashboard", use_container_width=True):
        st.session_state.current_user["onboarding_completed"] = True
        st.session_state.page = "dashboard"
        
        # Refresh user profile from API to get updated experience level and other changes
        updated_user = st.session_state.api_client.get_user_by_id(st.session_state.current_user["user_id"])
        if updated_user and "error" not in updated_user:
            st.session_state.current_user.update(updated_user)
        
        if "onboarding_state" in st.session_state:
            del st.session_state.onboarding_state
        
        st.rerun()


def process_onboarding_response(step: str, response_data: Dict[str, Any]):
    """Process onboarding step response and move to next step."""
    if not st.session_state.current_user:
        st.error("User session lost")
        return
    
    user_id = st.session_state.current_user["user_id"]
    
    # Process the step
    result = st.session_state.api_client.process_onboarding_step(user_id, step, response_data)
    
    if result and "error" not in result:
        # Update onboarding state
        st.session_state.onboarding_state = result
        st.rerun()
    else:
        st.error(f"Failed to process step: {result.get('detail', 'Unknown error') if result else 'No response'}")


def render_progress_indicator(current_step: str):
    """Render progress indicator for onboarding."""
    steps = [
        "welcome",
        "experience_assessment", 
        "learning_preferences",
        "goal_setting",
        "plan_selection",
        "session_preferences",
        "completion"
    ]
    
    current_index = steps.index(current_step) if current_step in steps else 0
    progress = (current_index / (len(steps) - 1)) * 100
    
    st.progress(progress / 100)
    st.markdown(f"Step {current_index + 1} of {len(steps)}: {current_step.replace('_', ' ').title()}")