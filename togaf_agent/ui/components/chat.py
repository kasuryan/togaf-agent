"""
Chat interface components for conversing with the TOGAF Agent.
"""

import streamlit as st
from typing import Dict, Any, List
import time


def render_chat_interface():
    """Render the main chat interface."""
    if not st.session_state.current_user:
        st.error("Please login first")
        return
    
    user = st.session_state.current_user
    user_id = user["user_id"]
    
    st.markdown('<h1 style="text-align: center; color: #1f77b4;">💬 Chat with TOGAF Agent</h1>', 
                unsafe_allow_html=True)
    
    # Initialize chat session if needed
    if "chat_session_id" not in st.session_state:
        initialize_chat_session(user_id)
    
    # Initialize follow-up suggestions in session state
    if "follow_up_suggestions" not in st.session_state:
        st.session_state.follow_up_suggestions = []
    if "suggestion_counter" not in st.session_state:
        st.session_state.suggestion_counter = 0
    
    # Chat interface layout
    render_chat_header()
    render_chat_history()
    render_follow_up_suggestions()  # Render outside form context
    render_chat_input()
    render_chat_sidebar()


def initialize_chat_session(user_id: str):
    """Initialize a new chat session."""
    # Check if user has an active session
    active_session = st.session_state.api_client.get_user_active_session(user_id)
    
    if active_session and active_session.get("active_session"):
        st.session_state.chat_session_id = active_session["active_session"]
        st.session_state.chat_messages = []
        load_chat_history()
    else:
        # Create new conversation session
        result = st.session_state.api_client.create_conversation_session(user_id, "learning")
        
        if result and "error" not in result:
            st.session_state.chat_session_id = result["session_id"]
            st.session_state.chat_messages = []
            
            # Add welcome message
            st.session_state.chat_messages.append({
                "role": "agent",
                "content": f"Hello {st.session_state.current_user.get('username', 'there')}! I'm your TOGAF learning assistant. I can help you with:\n\n" +
                          "• 📚 Understanding TOGAF concepts\n" +
                          "• 🎯 Exam preparation and practice questions\n" +
                          "• 📊 Explaining complex enterprise architecture topics\n" +
                          "• 🗂️ Navigating your learning plan\n\n" +
                          "What would you like to learn about today?",
                "timestamp": time.time()
            })
        else:
            st.error("Failed to create chat session")


def load_chat_history():
    """Load existing chat history."""
    if "chat_session_id" not in st.session_state:
        return
    
    history = st.session_state.api_client.get_conversation_history(
        st.session_state.chat_session_id, 
        limit=20
    )
    
    if history and "messages" in history:
        st.session_state.chat_messages = []
        
        for msg in history["messages"]:
            role = "user" if msg["message_type"] == "user_question" else "agent"
            st.session_state.chat_messages.append({
                "role": role,
                "content": msg["content"],
                "timestamp": msg["timestamp"]
            })


def render_chat_header():
    """Render chat interface header with controls."""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("Ask me anything about TOGAF, enterprise architecture, or exam preparation!")
    
    with col2:
        if st.button("🎯 Generate Exam Question", use_container_width=True):
            generate_exam_question()
    
    with col3:
        if st.button("🔄 New Chat", use_container_width=True):
            start_new_chat()


def render_chat_history():
    """Render the chat message history."""
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.chat_messages:
            render_message(message)
    
    # Auto-scroll to bottom
    if st.session_state.chat_messages:
        st.empty()


def render_message(message: Dict[str, Any]):
    """Render a single chat message."""
    role = message["role"]
    content = message["content"]
    
    if role == "user":
        # User message (right-aligned)
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; margin: 10px 0;">
            <div style="background-color: #007bff; color: white; padding: 10px 15px; 
                        border-radius: 15px 15px 5px 15px; max-width: 70%; word-wrap: break-word;">
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # Agent message (left-aligned)
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-start; margin: 10px 0;">
            <div style="background-color: #f8f9fa; color: #333; padding: 10px 15px; 
                        border-radius: 15px 15px 15px 5px; max-width: 70%; word-wrap: break-word;
                        border-left: 3px solid #1f77b4;">
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Check if message contains visual content (mermaid diagrams)
        if "```mermaid" in content:
            st.info("💡 This response contains a diagram that would be rendered in a full implementation!")


def render_chat_input():
    """Render the chat input area."""
    st.markdown("---")
    
    # Quick action buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("❓ What is ADM?", use_container_width=True):
            st.session_state.follow_up_suggestions = []  # Clear suggestions
            send_message("What is the TOGAF Architecture Development Method (ADM)?")
    
    with col2:
        if st.button("📊 Explain Phases", use_container_width=True):
            st.session_state.follow_up_suggestions = []  # Clear suggestions
            send_message("Can you explain the different phases of the TOGAF ADM?")
    
    with col3:
        if st.button("🎯 Exam Tips", use_container_width=True):
            st.session_state.follow_up_suggestions = []  # Clear suggestions
            send_message("What are some tips for preparing for the TOGAF Foundation exam?")
    
    with col4:
        if st.button("📚 My Progress", use_container_width=True):
            st.session_state.follow_up_suggestions = []  # Clear suggestions
            send_message("How am I doing with my TOGAF learning progress?")
    
    # Main chat input
    with st.form("chat_form", clear_on_submit=True):
        col_input, col_send = st.columns([4, 1])
        
        with col_input:
            user_input = st.text_input(
                "Type your message...",
                placeholder="Ask me about TOGAF concepts, exam questions, or your learning plan",
                label_visibility="collapsed"
            )
        
        with col_send:
            submitted = st.form_submit_button("Send 📤", use_container_width=True, type="primary")
        
        if submitted and user_input.strip():
            # Clear any existing follow-up suggestions when user types new message
            st.session_state.follow_up_suggestions = []
            send_message(user_input)


def render_chat_sidebar():
    """Render chat sidebar with additional options."""
    with st.sidebar:
        st.markdown("### 💬 Chat Options")
        
        # Explanation depth selector
        detail_level = st.selectbox(
            "Explanation Detail",
            ["adaptive", "brief", "moderate", "detailed"],
            help="Choose how detailed you want the explanations"
        )
        st.session_state.detail_level = detail_level
        
        # Topic focus
        st.markdown("### 🎯 Quick Topics")
        
        quick_topics = [
            "ADM Overview",
            "Preliminary Phase", 
            "Phase A: Architecture Vision",
            "Business Architecture",
            "Data Architecture",
            "Application Architecture",
            "Technology Architecture",
            "Architecture Governance",
            "Implementation & Migration",
            "Requirements Management"
        ]
        
        selected_topic = st.selectbox("Jump to Topic", ["Select a topic..."] + quick_topics)
        
        if selected_topic != "Select a topic...":
            if st.button("📖 Learn About This Topic", use_container_width=True):
                st.session_state.follow_up_suggestions = []  # Clear suggestions
                send_message(f"Please explain {selected_topic} in TOGAF")
        
        # Chat statistics
        st.markdown("### 📊 Chat Stats")
        if "chat_messages" in st.session_state:
            user_messages = len([m for m in st.session_state.chat_messages if m["role"] == "user"])
            agent_messages = len([m for m in st.session_state.chat_messages if m["role"] == "agent"])
            
            st.metric("Questions Asked", user_messages)
            st.metric("Responses Received", agent_messages)


def send_message(content: str):
    """Send a message and get AI response."""
    if not content.strip():
        return
    
    if "chat_session_id" not in st.session_state:
        st.error("No active chat session")
        return
    
    user_id = st.session_state.current_user["user_id"]
    session_id = st.session_state.chat_session_id
    
    # Add user message to chat
    user_message = {
        "role": "user",
        "content": content,
        "timestamp": time.time()
    }
    st.session_state.chat_messages.append(user_message)
    
    # Log message in session
    st.session_state.api_client.add_message(session_id, "user_question", content)
    
    # Show typing indicator
    with st.spinner("🤔 Thinking..."):
        # Get AI response
        detail_level = getattr(st.session_state, 'detail_level', 'adaptive')
        
        # Check if this is a request for explanation of a specific concept
        if any(word in content.lower() for word in ["explain", "what is", "define"]):
            # Extract concept (simplified approach)
            concept = extract_concept_from_message(content)
            if concept:
                response = st.session_state.api_client.get_concept_explanation(
                    concept, user_id, session_id, detail_level
                )
            else:
                response = st.session_state.api_client.send_chat_message(
                    content, user_id, session_id
                )
        else:
            response = st.session_state.api_client.send_chat_message(
                content, user_id, session_id
            )
    
    if response and "error" not in response:
        # Add agent response to chat
        agent_content = response.get("primary_content", "Sorry, I couldn't generate a response.")
        
        # Add visual content if available
        if response.get("visual_content"):
            agent_content += f"\n\n{response['visual_content']}"
        
        agent_message = {
            "role": "agent", 
            "content": agent_content,
            "timestamp": time.time()
        }
        st.session_state.chat_messages.append(agent_message)
        
        # Log agent response in session
        st.session_state.api_client.add_message(session_id, "agent_response", agent_content)
        
        # Store suggested follow-up questions in session state
        if response.get("suggested_next_questions"):
            st.session_state.follow_up_suggestions = response["suggested_next_questions"][:3]  # Max 3 suggestions
            # Increment counter to ensure new button keys
            if "suggestion_counter" in st.session_state:
                st.session_state.suggestion_counter += 1
        else:
            st.session_state.follow_up_suggestions = []
        
        st.rerun()
    else:
        error_msg = response.get("detail", "Failed to get response") if response else "No response received"
        st.error(f"Error: {error_msg}")


def generate_exam_question():
    """Generate an exam question for the user."""
    user_id = st.session_state.current_user["user_id"]
    
    with st.spinner("🎯 Generating exam question..."):
        question = st.session_state.api_client.generate_exam_question(user_id)
    
    if question and "error" not in question:
        # Format exam question as a chat message
        question_content = f"""**📝 Practice Question:**

{question.get('question', 'Question not available')}

A) {question.get('options', {}).get('A', 'Option A')}
B) {question.get('options', {}).get('B', 'Option B')}
C) {question.get('options', {}).get('C', 'Option C')}
D) {question.get('options', {}).get('D', 'Option D')}

*Think about your answer, then ask me for the correct answer and explanation!*

Topic: {question.get('topic_id', 'Unknown')} | Difficulty: {question.get('difficulty', 'Unknown')}"""
        
        agent_message = {
            "role": "agent",
            "content": question_content,
            "timestamp": time.time()
        }
        st.session_state.chat_messages.append(agent_message)
        st.rerun()
    else:
        st.error("Failed to generate exam question")


def start_new_chat():
    """Start a new chat session."""
    # End current session
    if "chat_session_id" in st.session_state:
        st.session_state.api_client.end_conversation_session(st.session_state.chat_session_id)
    
    # Clear session state
    if "chat_session_id" in st.session_state:
        del st.session_state.chat_session_id
    if "chat_messages" in st.session_state:
        del st.session_state.chat_messages
    if "follow_up_suggestions" in st.session_state:
        del st.session_state.follow_up_suggestions
    if "suggestion_counter" in st.session_state:
        del st.session_state.suggestion_counter
    
    # Initialize new session
    initialize_chat_session(st.session_state.current_user["user_id"])
    st.rerun()


def extract_concept_from_message(message: str) -> str:
    """Extract TOGAF concept from user message (simplified)."""
    # This is a simplified approach - in production, you'd use NLP
    togaf_concepts = [
        "ADM", "Architecture Development Method",
        "Preliminary Phase", "Phase A", "Phase B", "Phase C", "Phase D",
        "Phase E", "Phase F", "Phase G", "Phase H",
        "Requirements Management",
        "Business Architecture", "Data Architecture", 
        "Application Architecture", "Technology Architecture",
        "Architecture Governance", "Architecture Board",
        "Enterprise Continuum", "Architecture Repository",
        "TOGAF", "Enterprise Architecture"
    ]
    
    message_lower = message.lower()
    for concept in togaf_concepts:
        if concept.lower() in message_lower:
            return concept
    
    return ""


def render_follow_up_suggestions():
    """Render follow-up question suggestions from session state."""
    suggestions = st.session_state.get("follow_up_suggestions", [])
    
    if not suggestions:
        return
    
    st.markdown("**💡 Suggested follow-up questions:**")
    
    # Use stable keys based on content hash for consistent button behavior
    if "suggestion_counter" not in st.session_state:
        st.session_state.suggestion_counter = 0
    
    cols = st.columns(len(suggestions))
    
    for i, suggestion in enumerate(suggestions):
        with cols[i]:
            # Create stable key based on suggestion content
            suggestion_hash = hash(suggestion) % 10000  # Keep hash reasonable size
            button_key = f"followup_{i}_{suggestion_hash}_{st.session_state.suggestion_counter}"
            
            if st.button(f"❓ {suggestion}", key=button_key, use_container_width=True):
                # Clear suggestions and send message
                st.session_state.follow_up_suggestions = []
                st.session_state.suggestion_counter += 1  # Increment for next set
                send_message(suggestion)
                st.rerun()  # Force rerun to process the message