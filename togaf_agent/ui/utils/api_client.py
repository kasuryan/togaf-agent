"""
API client for communicating with the TOGAF Agent FastAPI backend.
"""

import requests
import streamlit as st
from typing import Dict, Any, Optional, List
import json


class TOGAFAPIClient:
    """Client for interacting with TOGAF Agent API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make HTTP request with error handling."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code < 400:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {"message": "Success"}
            else:
                error_data = {"error": f"HTTP {response.status_code}"}
                try:
                    error_detail = response.json()
                    error_data.update(error_detail)
                except json.JSONDecodeError:
                    error_data["detail"] = response.text
                
                return error_data
        
        except requests.RequestException as e:
            return {"error": "Connection failed", "detail": str(e)}
    
    # Health and System
    def get_health(self) -> Dict[str, Any]:
        """Get API health status."""
        return self._make_request("GET", "/health") or {}
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        return self._make_request("GET", "/api/v1/system/info") or {}
    
    # User Management
    def create_user(self, username: str, email: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create a new user."""
        data = {"username": username}
        if email:
            data["email"] = email
        
        return self._make_request("POST", "/api/v1/users/", json=data)
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        return self._make_request("GET", f"/api/v1/users/{user_id}")
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        return self._make_request("GET", f"/api/v1/users/username/{username}")
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user profile."""
        return self._make_request("PUT", f"/api/v1/users/{user_id}", json=updates)
    
    def get_user_statistics(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user statistics."""
        return self._make_request("GET", f"/api/v1/users/{user_id}/statistics")
    
    def get_user_learning_plans(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user learning plans."""
        return self._make_request("GET", f"/api/v1/users/{user_id}/learning-plans")
    
    def get_current_topic(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current topic in user's learning plan."""
        return self._make_request("GET", f"/api/v1/users/{user_id}/current-topic")
    
    def mark_topic_complete(self, user_id: str, topic_id: str) -> Optional[Dict[str, Any]]:
        """Mark a topic as completed."""
        return self._make_request("POST", f"/api/v1/users/{user_id}/topics/{topic_id}/complete")
    
    def skip_topic(self, user_id: str, topic_id: str) -> Optional[Dict[str, Any]]:
        """Skip a topic."""
        return self._make_request("POST", f"/api/v1/users/{user_id}/topics/{topic_id}/skip")
    
    def get_plan_overview(self, user_id: str, plan_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get learning plan overview."""
        params = {"plan_id": plan_id} if plan_id else None
        return self._make_request("GET", f"/api/v1/users/{user_id}/plan-overview", params=params)
    
    def reset_learning_progress(self, user_id: str, reset_type: str = "progress_only") -> Optional[Dict[str, Any]]:
        """Reset user's learning progress."""
        return self._make_request("POST", f"/api/v1/users/{user_id}/reset-learning", params={"reset_type": reset_type})
    
    # Onboarding
    def start_onboarding(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Start onboarding process."""
        return self._make_request("POST", "/api/v1/onboarding/start", json={"user_id": user_id})
    
    def process_onboarding_step(self, user_id: str, step: str, response_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process onboarding step."""
        data = {
            "user_id": user_id,
            "step": step,
            "response_data": response_data
        }
        return self._make_request("POST", "/api/v1/onboarding/step", json=data)
    
    def get_onboarding_progress(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get onboarding progress."""
        return self._make_request("GET", f"/api/v1/onboarding/progress/{user_id}")
    
    def get_onboarding_steps(self) -> Optional[Dict[str, Any]]:
        """Get list of onboarding steps."""
        return self._make_request("GET", "/api/v1/onboarding/steps")
    
    # Learning and Progress
    def start_learning_session(self, user_id: str, session_type: str = "general") -> Optional[Dict[str, Any]]:
        """Start a learning session."""
        data = {"user_id": user_id, "session_type": session_type}
        return self._make_request("POST", "/api/v1/learning/sessions/start", json=data)
    
    def end_learning_session(self, session_id: str, satisfaction_score: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """End a learning session."""
        data = {}
        if satisfaction_score is not None:
            data["satisfaction_score"] = satisfaction_score
        
        return self._make_request("POST", f"/api/v1/learning/sessions/{session_id}/end", json=data)
    
    def get_progress_analytics(self, user_id: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Get progress analytics."""
        params = {"force_refresh": force_refresh} if force_refresh else None
        return self._make_request("GET", f"/api/v1/learning/analytics/{user_id}", params=params)
    
    def get_learning_recommendations(self, user_id: str, count: int = 3) -> Optional[Dict[str, Any]]:
        """Get learning recommendations."""
        params = {"count": count}
        return self._make_request("GET", f"/api/v1/learning/recommendations/{user_id}", params=params)
    
    def get_learning_insights(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get learning insights."""
        return self._make_request("GET", f"/api/v1/learning/insights/{user_id}")
    
    def update_topic_proficiency(self, user_id: str, topic_id: str, performance_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update topic proficiency."""
        data = {
            "user_id": user_id,
            "topic_id": topic_id,
            "performance_data": performance_data
        }
        return self._make_request("POST", "/api/v1/learning/proficiency/update", json=data)
    
    # Session Management
    def create_conversation_session(self, user_id: str, conversation_mode: str = "learning", 
                                  initial_context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Create a conversation session."""
        data = {
            "user_id": user_id,
            "conversation_mode": conversation_mode
        }
        if initial_context:
            data["initial_context"] = initial_context
        
        return self._make_request("POST", "/api/v1/sessions/create", json=data)
    
    def get_conversation_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation session details."""
        return self._make_request("GET", f"/api/v1/sessions/{session_id}")
    
    def add_message(self, session_id: str, message_type: str, content: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Add message to conversation session."""
        data = {
            "message_type": message_type,
            "content": content
        }
        if metadata:
            data["metadata"] = metadata
        
        return self._make_request("POST", f"/api/v1/sessions/{session_id}/messages", json=data)
    
    def get_conversation_history(self, session_id: str, limit: Optional[int] = None, 
                               message_types: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Get conversation history."""
        params = {}
        if limit:
            params["limit"] = limit
        if message_types:
            params["message_types"] = message_types
        
        return self._make_request("GET", f"/api/v1/sessions/{session_id}/messages", params=params)
    
    def get_user_active_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's active session."""
        return self._make_request("GET", f"/api/v1/sessions/user/{user_id}/active")
    
    def end_conversation_session(self, session_id: str, satisfaction_score: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """End conversation session."""
        params = {}
        if satisfaction_score is not None:
            params["satisfaction_score"] = satisfaction_score
        
        return self._make_request("POST", f"/api/v1/sessions/{session_id}/end", params=params)
    
    # Chat and AI Responses
    def send_chat_message(self, user_query: str, user_id: str, session_id: str, 
                         context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Send chat message and get AI response."""
        data = {
            "user_query": user_query,
            "user_id": user_id,
            "session_id": session_id
        }
        if context:
            data["context"] = context
        
        return self._make_request("POST", "/api/v1/chat/message", json=data)
    
    def get_concept_explanation(self, concept: str, user_id: str, session_id: str, 
                              detail_level: str = "adaptive") -> Optional[Dict[str, Any]]:
        """Get explanation of a concept."""
        data = {
            "concept": concept,
            "user_id": user_id,
            "session_id": session_id,
            "detail_level": detail_level
        }
        return self._make_request("POST", "/api/v1/chat/explain", json=data)
    
    def generate_exam_question(self, user_id: str, topic_id: Optional[str] = None, 
                             difficulty: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Generate exam question."""
        data = {"user_id": user_id}
        if topic_id:
            data["topic_id"] = topic_id
        if difficulty:
            data["difficulty"] = difficulty
        
        return self._make_request("POST", "/api/v1/chat/exam-question", json=data)