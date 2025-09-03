"""
Main TOGAF Tutor orchestrator that coordinates all system components.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from ..utils.config import load_settings, Settings
from ..utils.openai_client import OpenAIClient
from ..user_management.user_profile import UserProfileManager
from ..user_management.onboarding import TOGAFOnboardingSystem
from ..user_management.progress_tracker import ProgressTracker
from ..conversation.session_manager import SessionManager, ConversationMode
from ..conversation.adaptive_agent import AdaptiveAgent
from ..knowledge_base.semantic_search import TOGAFSemanticSearch
from ..knowledge_base.pdf_processor import PDFProcessor
from ..knowledge_base.vector_store import TOGAFVectorStore


logger = logging.getLogger(__name__)


class TOGAFTutor:
    """
    Main orchestrator for the TOGAF learning and certification agent.
    
    This class coordinates all system components to provide a unified
    learning experience for TOGAF students.
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the TOGAF Tutor with all required components."""
        self.settings = settings or load_settings()
        self.is_initialized = False
        
        # Core components
        self.openai_client: Optional[OpenAIClient] = None
        self.profile_manager: Optional[UserProfileManager] = None
        self.onboarding_system: Optional[TOGAFOnboardingSystem] = None
        self.progress_tracker: Optional[ProgressTracker] = None
        self.session_manager: Optional[SessionManager] = None
        self.semantic_search: Optional[TOGAFSemanticSearch] = None
        self.adaptive_agent: Optional[AdaptiveAgent] = None
        
        # Knowledge base components
        self.pdf_processor: Optional[PDFProcessor] = None
        self.vector_store: Optional[TOGAFVectorStore] = None
    
    async def initialize(self) -> bool:
        """Initialize all system components."""
        try:
            logger.info("Initializing TOGAF Tutor system...")
            
            # Initialize OpenAI client
            self.openai_client = OpenAIClient(self.settings)
            api_valid = await self.openai_client.validate_api_key_async()
            
            if not api_valid:
                logger.warning("OpenAI API key validation failed - some features may not work")
            
            # Initialize user management components
            self.profile_manager = UserProfileManager()
            self.onboarding_system = TOGAFOnboardingSystem(self.profile_manager)
            self.progress_tracker = ProgressTracker(self.profile_manager)
            
            # Initialize conversation management
            self.session_manager = SessionManager(self.profile_manager)
            
            # Initialize knowledge base components
            self.pdf_processor = PDFProcessor(
                extract_images=True,
                save_images=True,
                image_dir=self.settings.knowledge_base_dir / "images"
            )
            
            self.vector_store = TOGAFVectorStore(self.settings)
            self.semantic_search = TOGAFSemanticSearch(self.settings)
            
            # Initialize adaptive agent (requires all other components)
            self.adaptive_agent = AdaptiveAgent(
                self.openai_client,
                self.semantic_search,
                self.progress_tracker,
                self.session_manager
            )
            
            self.is_initialized = True
            logger.info("TOGAF Tutor system initialized successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize TOGAF Tutor: {e}")
            return False
    
    def _ensure_initialized(self):
        """Ensure system is initialized before operations."""
        if not self.is_initialized:
            raise RuntimeError("TOGAF Tutor system not initialized. Call initialize() first.")
    
    # User Management Operations
    
    async def create_user(self, username: str, email: Optional[str] = None) -> Dict[str, Any]:
        """Create a new user and start onboarding."""
        self._ensure_initialized()
        
        try:
            # Create user profile
            profile = self.profile_manager.create_profile(username, email)
            
            # Start onboarding process
            onboarding_result = self.onboarding_system.start_onboarding(profile.user_id)
            
            return {
                "success": True,
                "user_id": profile.user_id,
                "username": profile.username,
                "onboarding_started": "error" not in onboarding_result,
                "onboarding_step": onboarding_result.get("step") if "error" not in onboarding_result else None
            }
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_user_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive dashboard data for a user."""
        self._ensure_initialized()
        
        try:
            # Get user profile
            profile = self.profile_manager.get_profile(user_id)
            if not profile:
                return {"success": False, "error": "User not found"}
            
            # Get analytics and insights
            analytics = self.progress_tracker.get_progress_analytics(user_id)
            insights = self.progress_tracker.get_learning_insights(user_id)
            statistics = self.profile_manager.get_user_statistics(user_id)
            
            # Get current learning status
            current_topic = self.profile_manager.get_current_topic(user_id)
            recommendations = self.progress_tracker.get_next_recommended_topics(user_id, 3)
            
            return {
                "success": True,
                "user_profile": {
                    "user_id": profile.user_id,
                    "username": profile.username,
                    "experience_level": profile.experience_level.value,
                    "overall_proficiency": profile.overall_proficiency,
                    "target_certification": profile.target_certification.value if profile.target_certification else None,
                    "exam_preparation_mode": profile.exam_preparation_mode
                },
                "analytics": analytics.model_dump() if analytics else None,
                "insights": insights,
                "statistics": statistics,
                "current_topic": current_topic,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Failed to get user dashboard: {e}")
            return {"success": False, "error": str(e)}
    
    # Learning and Conversation Operations
    
    async def start_learning_session(self, user_id: str, 
                                   conversation_mode: ConversationMode = ConversationMode.LEARNING,
                                   initial_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Start a comprehensive learning session."""
        self._ensure_initialized()
        
        try:
            # Start progress tracking session
            tracking_session_id = self.progress_tracker.start_learning_session(user_id, "learning")
            
            # Create conversation session
            conversation_session_id = self.session_manager.create_session(
                user_id, conversation_mode, initial_context
            )
            
            # Get user context for personalized welcome
            profile = self.profile_manager.get_profile(user_id)
            session_context = self.session_manager.get_session_context(conversation_session_id)
            
            return {
                "success": True,
                "tracking_session_id": tracking_session_id,
                "conversation_session_id": conversation_session_id,
                "user_context": {
                    "experience_level": profile.experience_level.value if profile else "beginner",
                    "target_certification": profile.target_certification.value if profile and profile.target_certification else "foundation",
                    "current_topic": session_context.get("conversation_context", {}).get("current_topic")
                },
                "welcome_message": self._generate_welcome_message(profile, session_context)
            }
            
        except Exception as e:
            logger.error(f"Failed to start learning session: {e}")
            return {"success": False, "error": str(e)}
    
    async def process_user_query(self, user_id: str, session_id: str, query: str,
                               context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a user query and generate adaptive response."""
        self._ensure_initialized()
        
        try:
            # Log the user query
            self.session_manager.add_message(session_id, "user_question", query)
            
            # Generate adaptive response
            response = await self.adaptive_agent.generate_adaptive_response(
                query, user_id, session_id, context
            )
            
            # Log the agent response
            self.session_manager.add_message(session_id, "agent_response", response.primary_content)
            
            # Update progress tracking
            if response.topics_addressed:
                for topic in response.topics_addressed:
                    # Log topic interaction (assuming active tracking session)
                    active_session = getattr(self.progress_tracker, '_active_sessions', {})
                    tracking_session_id = None
                    
                    for ts_id, session in active_session.items():
                        if session.user_id == user_id:
                            tracking_session_id = ts_id
                            break
                    
                    if tracking_session_id:
                        self.progress_tracker.log_topic_interaction(
                            tracking_session_id, topic, "question", True
                        )
            
            return {
                "success": True,
                "response": {
                    "primary_content": response.primary_content,
                    "visual_content": response.visual_content,
                    "topics_addressed": response.topics_addressed,
                    "concepts_explained": response.concepts_explained,
                    "difficulty_level": response.difficulty_level.value,
                    "suggested_follow_ups": response.suggested_next_questions,
                    "related_topics": response.related_topics
                },
                "session_updated": True
            }
            
        except Exception as e:
            logger.error(f"Failed to process user query: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_personalized_content(self, user_id: str, content_type: str,
                                          topic: Optional[str] = None,
                                          difficulty: Optional[str] = None) -> Dict[str, Any]:
        """Generate personalized learning content."""
        self._ensure_initialized()
        
        try:
            if content_type == "exam_question":
                # Generate exam question
                question = await self.adaptive_agent.generate_exam_question(user_id, topic, difficulty)
                
                return {
                    "success": True,
                    "content_type": "exam_question",
                    "content": question
                }
            
            elif content_type == "concept_explanation":
                if not topic:
                    return {"success": False, "error": "Topic required for concept explanation"}
                
                # Create temporary session for explanation
                temp_session_id = self.session_manager.create_session(user_id, ConversationMode.LEARNING)
                
                explanation = await self.adaptive_agent.provide_explanation(
                    topic, user_id, temp_session_id, difficulty or "adaptive"
                )
                
                # Clean up temporary session
                self.session_manager.end_session(temp_session_id)
                
                return {
                    "success": True,
                    "content_type": "concept_explanation",
                    "content": {
                        "primary_content": explanation.primary_content,
                        "visual_content": explanation.visual_content,
                        "concepts_explained": explanation.concepts_explained,
                        "difficulty_level": explanation.difficulty_level.value
                    }
                }
            
            else:
                return {"success": False, "error": f"Unknown content type: {content_type}"}
                
        except Exception as e:
            logger.error(f"Failed to generate personalized content: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_learning_progress(self, user_id: str, topic_id: str,
                                     performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user's learning progress for a topic."""
        self._ensure_initialized()
        
        try:
            # Update topic proficiency
            success = self.progress_tracker.update_topic_proficiency(
                user_id, topic_id, performance_data
            )
            
            if not success:
                return {"success": False, "error": "Failed to update proficiency"}
            
            # Get updated analytics
            analytics = self.progress_tracker.get_progress_analytics(user_id, force_refresh=True)
            
            # Get new recommendations
            recommendations = self.progress_tracker.get_next_recommended_topics(user_id, 3)
            
            return {
                "success": True,
                "proficiency_updated": True,
                "new_analytics": analytics.model_dump() if analytics else None,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Failed to update learning progress: {e}")
            return {"success": False, "error": str(e)}
    
    # Learning Plan Management
    
    async def create_learning_plan(self, user_id: str, plan_type: str,
                                 custom_topics: Optional[List[str]] = None,
                                 plan_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a structured learning plan for a user."""
        self._ensure_initialized()
        
        try:
            from ..user_management.user_profile import PlanType
            
            # Create the learning plan
            plan_id = self.profile_manager.create_structured_plan(
                user_id, PlanType(plan_type), custom_topics, plan_name
            )
            
            if not plan_id:
                return {"success": False, "error": "Failed to create learning plan"}
            
            # Get plan overview
            plan_overview = self.profile_manager.get_plan_overview(user_id, plan_id)
            
            return {
                "success": True,
                "plan_id": plan_id,
                "plan_overview": plan_overview
            }
            
        except Exception as e:
            logger.error(f"Failed to create learning plan: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_learning_plan_status(self, user_id: str, 
                                     plan_id: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed learning plan status."""
        self._ensure_initialized()
        
        try:
            plan_overview = self.profile_manager.get_plan_overview(user_id, plan_id)
            
            if not plan_overview:
                return {"success": False, "error": "Learning plan not found"}
            
            current_topic = self.profile_manager.get_current_topic(user_id)
            recommendations = self.progress_tracker.get_next_recommended_topics(user_id, 5)
            
            return {
                "success": True,
                "plan_overview": plan_overview,
                "current_topic": current_topic,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Failed to get learning plan status: {e}")
            return {"success": False, "error": str(e)}
    
    # Knowledge Base Operations
    
    async def search_knowledge_base(self, query: str, user_id: Optional[str] = None,
                                  certification_level: Optional[str] = None,
                                  limit: int = 5) -> Dict[str, Any]:
        """Search the TOGAF knowledge base."""
        self._ensure_initialized()
        
        try:
            from ..knowledge_base.metadata_schema import CertificationLevel
            
            # Determine certification level
            cert_level = None
            if certification_level:
                cert_level = CertificationLevel(certification_level)
            elif user_id:
                profile = self.profile_manager.get_profile(user_id)
                if profile and profile.target_certification:
                    cert_level = profile.target_certification
            
            # Perform search
            if cert_level:
                # Map certification level to user_goal string
                user_goal = "foundation" if cert_level.value == "foundation" else "practitioner"
                # Default user_level since we don't have profile context here
                results = await self.semantic_search.search_with_context(
                    query, 
                    user_level="intermediate", 
                    user_goal=user_goal, 
                    n_results=limit
                )
            else:
                # Use default SearchQuery with basic search
                from ..knowledge_base.semantic_search import SearchQuery
                search_query = SearchQuery(text=query, n_results=limit)
                results = await self.semantic_search.search(search_query)
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "result_count": len(results)
            }
            
        except Exception as e:
            logger.error(f"Failed to search knowledge base: {e}")
            return {"success": False, "error": str(e)}
    
    # System Operations
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        try:
            status = {
                "initialized": self.is_initialized,
                "timestamp": datetime.now().isoformat(),
                "components": {}
            }
            
            if self.is_initialized:
                # Check OpenAI connection
                api_valid = await self.openai_client.validate_api_key_async()
                status["components"]["openai"] = "healthy" if api_valid else "unhealthy"
                
                # Check other components
                components = [
                    ("profile_manager", self.profile_manager),
                    ("onboarding_system", self.onboarding_system),
                    ("progress_tracker", self.progress_tracker),
                    ("session_manager", self.session_manager),
                    ("semantic_search", self.semantic_search),
                    ("adaptive_agent", self.adaptive_agent)
                ]
                
                for name, component in components:
                    status["components"][name] = "healthy" if component else "not_initialized"
                
                # Get user statistics
                try:
                    all_profiles = self.profile_manager.list_all_profiles()
                    status["users"] = {
                        "total": len(all_profiles),
                        "onboarded": len([p for p in all_profiles if p.onboarding_completed])
                    }
                except Exception:
                    status["users"] = {"error": "Failed to get user stats"}
            
            return {"success": True, "status": status}
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {"success": False, "error": str(e)}
    
    async def cleanup_system(self) -> Dict[str, Any]:
        """Perform system cleanup operations."""
        self._ensure_initialized()
        
        try:
            cleanup_results = {}
            
            # Cleanup expired sessions
            if self.session_manager:
                expired_sessions = self.session_manager.cleanup_expired_sessions()
                cleanup_results["expired_sessions"] = expired_sessions
            
            # Additional cleanup operations could be added here
            
            return {
                "success": True,
                "cleanup_results": cleanup_results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup system: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_welcome_message(self, profile, session_context: Dict[str, Any]) -> str:
        """Generate a personalized welcome message."""
        if not profile:
            return "Welcome to your TOGAF learning journey!"
        
        username = profile.username
        experience_level = profile.experience_level.value
        target_cert = profile.target_certification.value if profile.target_certification else "Foundation"
        
        current_topic = session_context.get("conversation_context", {}).get("current_topic")
        
        welcome = f"Welcome back, {username}! 🎯\n\n"
        welcome += f"Experience Level: {experience_level.title()}\n"
        welcome += f"Target Certification: {target_cert.title()}\n"
        
        if current_topic:
            welcome += f"Current Focus: {current_topic.replace('_', ' ').title()}\n"
        
        welcome += "\nI'm here to help you master TOGAF! What would you like to explore today?"
        
        return welcome