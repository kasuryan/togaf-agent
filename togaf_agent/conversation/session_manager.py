"""
Context-aware session manager for TOGAF Agent conversations.
Manages conversation state, context, and learning continuity.
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field
from enum import Enum

from ..user_management.user_profile import UserProfile, UserProfileManager
from ..knowledge_base.metadata_schema import CertificationLevel


class SessionState(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXPIRED = "expired"


class ConversationMode(str, Enum):
    LEARNING = "learning"
    EXAM_PREP = "exam_prep"
    Q_AND_A = "q_and_a"
    ASSESSMENT = "assessment"
    REVIEW = "review"


class MessageType(str, Enum):
    USER_QUESTION = "user_question"
    AGENT_RESPONSE = "agent_response"
    SYSTEM_NOTIFICATION = "system_notification"
    PROGRESS_UPDATE = "progress_update"


class ConversationMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    message_type: MessageType
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Context information
    topic_context: Optional[str] = None
    certification_level: Optional[CertificationLevel] = None
    difficulty_level: str = "moderate"
    
    # Response quality metrics
    helpfulness_score: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    user_satisfaction: Optional[int] = Field(default=None, ge=1, le=5)


class ConversationContext(BaseModel):
    # Current learning context
    current_topic: Optional[str] = None
    current_certification_level: Optional[CertificationLevel] = None
    learning_objective: Optional[str] = None
    
    # Topic progression
    topics_discussed: List[str] = Field(default_factory=list)
    concepts_explained: List[str] = Field(default_factory=list)
    questions_asked: List[str] = Field(default_factory=list)
    
    # User understanding indicators
    comprehension_signals: Dict[str, float] = Field(default_factory=dict)  # concept -> understanding_level
    confusion_indicators: List[str] = Field(default_factory=list)  # concepts user finds difficult
    
    # Session flow
    conversation_mode: ConversationMode = ConversationMode.LEARNING
    follow_up_needed: List[str] = Field(default_factory=list)
    pending_explanations: List[str] = Field(default_factory=list)
    
    # Adaptive parameters
    current_difficulty_level: str = "moderate"
    explanation_depth: str = "moderate"
    use_examples: bool = True
    visual_aids_requested: bool = False


class ConversationSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    expires_at: datetime = Field(default_factory=lambda: datetime.now() + timedelta(hours=4))
    
    # Session state
    state: SessionState = SessionState.ACTIVE
    conversation_mode: ConversationMode = ConversationMode.LEARNING
    
    # Conversation history
    messages: List[ConversationMessage] = Field(default_factory=list)
    context: ConversationContext = Field(default_factory=ConversationContext)
    
    # Session metrics
    total_messages: int = 0
    user_questions: int = 0
    agent_responses: int = 0
    topics_covered: int = 0
    session_satisfaction: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    
    # Learning progress in this session
    concepts_learned: List[str] = Field(default_factory=list)
    skills_practiced: List[str] = Field(default_factory=list)
    assessment_scores: Dict[str, float] = Field(default_factory=dict)


class SessionManager:
    """Context-aware session manager for TOGAF learning conversations."""
    
    def __init__(self, profile_manager: UserProfileManager, 
                 sessions_dir: Path = Path("./user_data/conversation_sessions")):
        self.profile_manager = profile_manager
        self.sessions_dir = sessions_dir
        self.sessions_dir.mkdir(exist_ok=True)
        
        # In-memory session cache
        self._active_sessions: Dict[str, ConversationSession] = {}
        self._session_timeouts: Dict[str, datetime] = {}
        
        # Context windows for different conversation modes
        self.context_windows = {
            ConversationMode.LEARNING: 20,      # Last 20 messages
            ConversationMode.EXAM_PREP: 15,     # Focus on recent Q&A
            ConversationMode.Q_AND_A: 10,       # Quick context
            ConversationMode.ASSESSMENT: 5,     # Minimal context
            ConversationMode.REVIEW: 25         # Broader context for review
        }
    
    def create_session(self, user_id: str, 
                      conversation_mode: ConversationMode = ConversationMode.LEARNING,
                      initial_context: Optional[Dict[str, Any]] = None) -> str:
        """Create a new conversation session for a user."""
        profile = self.profile_manager.get_profile(user_id)
        if not profile:
            raise ValueError(f"User profile not found: {user_id}")
        
        session = ConversationSession(
            user_id=user_id,
            conversation_mode=conversation_mode
        )
        
        # Set initial context based on user profile
        self._initialize_session_context(session, profile, initial_context)
        
        # Cache session
        self._active_sessions[session.session_id] = session
        self._session_timeouts[session.session_id] = session.expires_at
        
        # Update user profile
        profile.current_session_id = session.session_id
        self.profile_manager.save_profile(profile)
        
        return session.session_id
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get an active session by ID."""
        # Check cache first
        if session_id in self._active_sessions:
            session = self._active_sessions[session_id]
            
            # Check if session expired
            if datetime.now() > session.expires_at:
                self._expire_session(session_id)
                return None
            
            return session
        
        # Try loading from disk
        return self._load_session(session_id)
    
    def add_message(self, session_id: str, message_type: MessageType, 
                   content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add a message to the conversation session."""
        session = self.get_session(session_id)
        if not session or session.state != SessionState.ACTIVE:
            return False
        
        # Create message
        message = ConversationMessage(
            message_type=message_type,
            content=content,
            metadata=metadata or {},
            topic_context=session.context.current_topic,
            certification_level=session.context.current_certification_level,
            difficulty_level=session.context.current_difficulty_level
        )
        
        # Add to session
        session.messages.append(message)
        session.total_messages += 1
        session.last_activity = datetime.now()
        
        # Update counters
        if message_type == MessageType.USER_QUESTION:
            session.user_questions += 1
        elif message_type == MessageType.AGENT_RESPONSE:
            session.agent_responses += 1
        
        # Update context based on message
        self._update_context_from_message(session, message)
        
        # Save session
        self._save_session(session)
        
        return True
    
    def update_context(self, session_id: str, context_updates: Dict[str, Any]) -> bool:
        """Update session context with new information."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Update context fields
        context = session.context
        
        if "current_topic" in context_updates:
            context.current_topic = context_updates["current_topic"]
            if context.current_topic not in context.topics_discussed:
                context.topics_discussed.append(context.current_topic)
                session.topics_covered += 1
        
        if "current_certification_level" in context_updates:
            context.current_certification_level = CertificationLevel(context_updates["current_certification_level"])
        
        if "learning_objective" in context_updates:
            context.learning_objective = context_updates["learning_objective"]
        
        if "conversation_mode" in context_updates:
            new_mode = ConversationMode(context_updates["conversation_mode"])
            session.conversation_mode = new_mode
            context.conversation_mode = new_mode
        
        if "difficulty_level" in context_updates:
            context.current_difficulty_level = context_updates["difficulty_level"]
        
        if "comprehension_signals" in context_updates:
            context.comprehension_signals.update(context_updates["comprehension_signals"])
        
        if "concepts_explained" in context_updates:
            new_concepts = context_updates["concepts_explained"]
            for concept in new_concepts:
                if concept not in context.concepts_explained:
                    context.concepts_explained.append(concept)
                    session.concepts_learned.append(concept)
        
        session.last_activity = datetime.now()
        self._save_session(session)
        
        return True
    
    def get_conversation_history(self, session_id: str, 
                               limit: Optional[int] = None,
                               message_types: Optional[List[MessageType]] = None) -> List[ConversationMessage]:
        """Get conversation history with optional filtering."""
        session = self.get_session(session_id)
        if not session:
            return []
        
        messages = session.messages
        
        # Filter by message types if specified
        if message_types:
            messages = [msg for msg in messages if msg.message_type in message_types]
        
        # Apply limit based on conversation mode context window
        if limit is None:
            limit = self.context_windows.get(session.conversation_mode, 20)
        
        return messages[-limit:] if limit > 0 else messages
    
    def get_session_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session context for agent responses."""
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Get user profile for additional context
        profile = self.profile_manager.get_profile(session.user_id)
        if not profile:
            return None
        
        # Build comprehensive context
        context = {
            "session_info": {
                "session_id": session_id,
                "conversation_mode": session.conversation_mode.value,
                "topics_covered": session.topics_covered,
                "total_messages": session.total_messages,
                "session_duration_minutes": int((session.last_activity - session.created_at).total_seconds() / 60)
            },
            "user_profile": {
                "experience_level": profile.experience_level.value,
                "learning_approach": profile.learning_approach.value,
                "target_certification": profile.target_certification.value if profile.target_certification else None,
                "exam_preparation_mode": profile.exam_preparation_mode,
                "overall_proficiency": profile.overall_proficiency
            },
            "conversation_context": session.context.model_dump(),
            "learning_preferences": {
                "learning_style": profile.conversation_preferences.learning_style.value,
                "explanation_depth": profile.conversation_preferences.explanation_depth,
                "use_examples": profile.conversation_preferences.use_examples,
                "use_diagrams": profile.conversation_preferences.use_diagrams,
                "interactive_mode": profile.conversation_preferences.interactive_mode
            },
            "recent_messages": [
                {
                    "type": msg.message_type.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "topic_context": msg.topic_context
                }
                for msg in self.get_conversation_history(session_id, limit=10)
            ]
        }
        
        return context
    
    def pause_session(self, session_id: str) -> bool:
        """Pause an active session."""
        session = self.get_session(session_id)
        if not session or session.state != SessionState.ACTIVE:
            return False
        
        session.state = SessionState.PAUSED
        session.last_activity = datetime.now()
        
        self._save_session(session)
        return True
    
    def resume_session(self, session_id: str) -> bool:
        """Resume a paused session."""
        session = self.get_session(session_id)
        if not session or session.state != SessionState.PAUSED:
            return False
        
        # Check if session hasn't expired
        if datetime.now() > session.expires_at:
            self._expire_session(session_id)
            return False
        
        session.state = SessionState.ACTIVE
        session.last_activity = datetime.now()
        
        self._save_session(session)
        return True
    
    def end_session(self, session_id: str, satisfaction_score: Optional[float] = None) -> bool:
        """End a session and save final state."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.state = SessionState.COMPLETED
        session.last_activity = datetime.now()
        
        if satisfaction_score:
            session.session_satisfaction = satisfaction_score
        
        # Update user profile
        profile = self.profile_manager.get_profile(session.user_id)
        if profile:
            profile.current_session_id = None
            
            # Update learning progress based on session
            for concept in session.concepts_learned:
                if concept not in profile.strengths:
                    profile.strengths.append(concept)
            
            self.profile_manager.save_profile(profile)
        
        # Save final session state
        self._save_session(session)
        
        # Remove from active cache
        self._active_sessions.pop(session_id, None)
        self._session_timeouts.pop(session_id, None)
        
        return True
    
    def get_user_active_session(self, user_id: str) -> Optional[str]:
        """Get the active session ID for a user."""
        profile = self.profile_manager.get_profile(user_id)
        if not profile or not profile.current_session_id:
            return None
        
        # Verify session is still active
        session = self.get_session(profile.current_session_id)
        if session and session.state == SessionState.ACTIVE:
            return profile.current_session_id
        
        return None
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions and return count cleaned."""
        expired_count = 0
        current_time = datetime.now()
        
        # Check active sessions
        expired_session_ids = [
            session_id for session_id, expires_at in self._session_timeouts.items()
            if current_time > expires_at
        ]
        
        for session_id in expired_session_ids:
            self._expire_session(session_id)
            expired_count += 1
        
        # Check disk sessions (basic cleanup)
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                expires_at_str = data.get('expires_at')
                if expires_at_str:
                    expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                    if current_time > expires_at:
                        session_file.unlink()
                        expired_count += 1
            except (json.JSONDecodeError, ValueError, KeyError):
                continue
        
        return expired_count
    
    def _initialize_session_context(self, session: ConversationSession, 
                                  profile: UserProfile, 
                                  initial_context: Optional[Dict[str, Any]]) -> None:
        """Initialize session context based on user profile."""
        context = session.context
        
        # Set target certification level
        context.current_certification_level = profile.target_certification or CertificationLevel.FOUNDATION
        
        # Set difficulty based on experience level
        difficulty_mapping = {
            "beginner": "basic",
            "intermediate": "moderate", 
            "advanced": "challenging",
            "expert": "advanced"
        }
        context.current_difficulty_level = difficulty_mapping.get(profile.experience_level.value, "moderate")
        
        # Set explanation preferences
        context.explanation_depth = profile.conversation_preferences.explanation_depth
        context.use_examples = profile.conversation_preferences.use_examples
        context.visual_aids_requested = profile.conversation_preferences.use_diagrams
        
        # Set current topic if user has an active learning plan
        if profile.active_plan_id:
            current_topic_data = self.profile_manager.get_current_topic(profile.user_id)
            if current_topic_data:
                context.current_topic = current_topic_data["topic"]["topic_id"]
                context.learning_objective = current_topic_data["topic"]["description"]
        
        # Apply initial context overrides
        if initial_context:
            for key, value in initial_context.items():
                if hasattr(context, key):
                    setattr(context, key, value)
    
    def _update_context_from_message(self, session: ConversationSession, 
                                   message: ConversationMessage) -> None:
        """Update session context based on message content."""
        context = session.context
        
        # Extract topics mentioned in the message
        # This would be enhanced with NLP in a real implementation
        content_lower = message.content.lower()
        
        # Basic topic detection
        togaf_topics = ["adm", "preliminary", "architecture", "business", "data", "application", 
                       "technology", "governance", "implementation", "migration"]
        
        for topic in togaf_topics:
            if topic in content_lower:
                if topic not in context.topics_discussed:
                    context.topics_discussed.append(topic)
        
        # Track questions for comprehension assessment
        if message.message_type == MessageType.USER_QUESTION:
            context.questions_asked.append(message.content)
            
            # Detect confusion indicators
            confusion_keywords = ["confused", "don't understand", "unclear", "complicated", "difficult"]
            if any(keyword in content_lower for keyword in confusion_keywords):
                if message.topic_context and message.topic_context not in context.confusion_indicators:
                    context.confusion_indicators.append(message.topic_context)
    
    def _save_session(self, session: ConversationSession) -> None:
        """Save session to disk."""
        session_file = self.sessions_dir / f"{session.session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session.model_dump(mode='json'), f, indent=2, default=str)
        
        # Update cache
        self._active_sessions[session.session_id] = session
    
    def _load_session(self, session_id: str) -> Optional[ConversationSession]:
        """Load session from disk."""
        session_file = self.sessions_dir / f"{session_id}.json"
        if not session_file.exists():
            return None
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            session = ConversationSession.model_validate(data)
            
            # Check if session expired
            if datetime.now() > session.expires_at:
                return None
            
            # Cache session
            self._active_sessions[session_id] = session
            self._session_timeouts[session_id] = session.expires_at
            
            return session
        
        except (json.JSONDecodeError, ValueError) as e:
            # Invalid session file
            return None
    
    def _expire_session(self, session_id: str) -> None:
        """Mark session as expired and clean up."""
        session = self._active_sessions.get(session_id)
        if session:
            session.state = SessionState.EXPIRED
            self._save_session(session)
        
        # Remove from cache
        self._active_sessions.pop(session_id, None)
        self._session_timeouts.pop(session_id, None)
    
    def get_session_statistics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get session statistics for a user over the specified period."""
        cutoff_date = datetime.now() - timedelta(days=days)
        user_sessions = []
        
        # Collect user sessions from disk
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if (data.get('user_id') == user_id and 
                    datetime.fromisoformat(data.get('created_at', '').replace('Z', '+00:00')) >= cutoff_date):
                    session = ConversationSession.model_validate(data)
                    user_sessions.append(session)
            except (json.JSONDecodeError, ValueError):
                continue
        
        if not user_sessions:
            return {}
        
        # Calculate statistics
        total_sessions = len(user_sessions)
        total_messages = sum(session.total_messages for session in user_sessions)
        total_topics = sum(session.topics_covered for session in user_sessions)
        
        avg_satisfaction = None
        satisfaction_scores = [s.session_satisfaction for s in user_sessions if s.session_satisfaction is not None]
        if satisfaction_scores:
            avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores)
        
        # Mode distribution
        mode_counts = {}
        for session in user_sessions:
            mode = session.conversation_mode.value
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "average_messages_per_session": total_messages / total_sessions if total_sessions > 0 else 0,
            "total_topics_covered": total_topics,
            "average_topics_per_session": total_topics / total_sessions if total_sessions > 0 else 0,
            "average_satisfaction": avg_satisfaction,
            "conversation_mode_distribution": mode_counts,
            "most_used_mode": max(mode_counts, key=mode_counts.get) if mode_counts else None
        }