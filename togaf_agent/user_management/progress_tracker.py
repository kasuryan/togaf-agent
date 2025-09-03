"""
Intelligent progress tracking with adaptive learning paths for TOGAF Agent.
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field
from enum import Enum

from .user_profile import (
    UserProfile, UserProfileManager, ExperienceLevel, TopicStatus,
    StructuredLearningPlan, LearningPlanTopic, TopicProgress
)
from ..knowledge_base.metadata_schema import CertificationLevel, FoundationPart


class LearningPathType(str, Enum):
    LINEAR = "linear"
    ADAPTIVE = "adaptive"
    PERSONALIZED = "personalized"
    EXAM_FOCUSED = "exam_focused"


class ProgressAnalytics(BaseModel):
    user_id: str
    analysis_date: datetime = Field(default_factory=datetime.now)
    
    # Overall progress metrics
    overall_completion: float = Field(default=0.0, ge=0.0, le=100.0)
    study_consistency: float = Field(default=0.0, ge=0.0, le=1.0)  # Based on streak and regularity
    learning_velocity: float = Field(default=1.0, ge=0.1, le=5.0)  # Topics per hour
    retention_rate: float = Field(default=0.0, ge=0.0, le=1.0)    # Quiz performance retention
    
    # Certification readiness
    foundation_readiness: float = Field(default=0.0, ge=0.0, le=1.0)
    practitioner_readiness: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Learning pattern insights
    peak_performance_times: List[str] = Field(default_factory=list)  # ["morning", "afternoon", "evening"]
    optimal_session_length: int = Field(default=30)  # minutes
    preferred_difficulty_progression: str = "gradual"  # "gradual", "mixed", "challenging"
    
    # Adaptive recommendations
    suggested_next_topics: List[str] = Field(default_factory=list)
    review_topics: List[str] = Field(default_factory=list)
    challenge_topics: List[str] = Field(default_factory=list)
    
    # Weak areas needing attention
    knowledge_gaps: Dict[str, float] = Field(default_factory=dict)  # topic_id -> gap_score
    improvement_focus: List[str] = Field(default_factory=list)


class LearningSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_minutes: int = 0
    
    # Session content
    topics_covered: List[str] = Field(default_factory=list)
    questions_asked: int = 0
    questions_answered_correctly: int = 0
    concepts_explained: List[str] = Field(default_factory=list)
    
    # Session quality metrics
    engagement_score: float = Field(default=0.0, ge=0.0, le=1.0)
    comprehension_score: float = Field(default=0.0, ge=0.0, le=1.0)
    satisfaction_score: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    
    # Adaptive insights
    difficulty_level_used: str = "moderate"
    learning_style_applied: str = "reading_writing"
    session_notes: str = ""


class AdaptiveLearningPath(BaseModel):
    path_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    path_type: LearningPathType
    created_date: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    # Path configuration
    target_certification: CertificationLevel
    estimated_completion_weeks: int = 8
    difficulty_progression: str = "adaptive"  # "linear", "adaptive", "custom"
    
    # Dynamic path structure
    current_topics: List[str] = Field(default_factory=list)  # Currently recommended topics
    completed_topics: List[str] = Field(default_factory=list)
    skipped_topics: List[str] = Field(default_factory=list)
    priority_topics: List[str] = Field(default_factory=list)  # High-priority based on gaps
    
    # Adaptation parameters
    performance_threshold: float = 0.7  # Minimum score to advance
    adaptation_sensitivity: float = 0.5  # How quickly to adapt (0-1)
    review_frequency: int = 3  # Review every N topics
    
    # Path effectiveness metrics
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    average_topic_completion_time: float = 60.0  # minutes
    path_satisfaction: float = Field(default=0.0, ge=0.0, le=5.0)


class ProgressTracker:
    """Intelligent progress tracking with adaptive learning path management."""
    
    def __init__(self, profile_manager: UserProfileManager, 
                 analytics_dir: Path = Path("./user_data/analytics")):
        self.profile_manager = profile_manager
        self.analytics_dir = analytics_dir
        self.analytics_dir.mkdir(exist_ok=True)
        
        self.sessions_dir = analytics_dir / "sessions"
        self.sessions_dir.mkdir(exist_ok=True)
        
        # In-memory caches for performance
        self._analytics_cache: Dict[str, ProgressAnalytics] = {}
        self._active_sessions: Dict[str, LearningSession] = {}
        self._learning_paths: Dict[str, AdaptiveLearningPath] = {}
    
    def start_learning_session(self, user_id: str, session_type: str = "general") -> str:
        """Start a new learning session for tracking."""
        session = LearningSession(user_id=user_id)
        session.session_notes = f"Session type: {session_type}"
        
        self._active_sessions[session.session_id] = session
        
        # Update user profile
        profile = self.profile_manager.get_profile(user_id)
        if profile:
            profile.current_session_id = session.session_id
            self.profile_manager.save_profile(profile)
        
        return session.session_id
    
    def end_learning_session(self, session_id: str, 
                           satisfaction_score: Optional[float] = None) -> bool:
        """End a learning session and save analytics."""
        session = self._active_sessions.get(session_id)
        if not session:
            return False
        
        session.end_time = datetime.now()
        session.duration_minutes = int((session.end_time - session.start_time).total_seconds() / 60)
        
        if satisfaction_score:
            session.satisfaction_score = satisfaction_score
        
        # Calculate engagement and comprehension scores
        session.engagement_score = self._calculate_engagement_score(session)
        session.comprehension_score = self._calculate_comprehension_score(session)
        
        # Save session to disk
        self._save_session(session)
        
        # Update user profile session stats
        self.profile_manager.update_session_stats(
            session.user_id, 
            session.duration_minutes, 
            session.topics_covered
        )
        
        # Update user analytics
        self._update_user_analytics(session.user_id)
        
        # Remove from active sessions
        del self._active_sessions[session_id]
        
        # Clear current session from profile
        profile = self.profile_manager.get_profile(session.user_id)
        if profile:
            profile.current_session_id = None
            self.profile_manager.save_profile(profile)
        
        return True
    
    def log_topic_interaction(self, session_id: str, topic_id: str, 
                            interaction_type: str, success: bool = True) -> bool:
        """Log user interaction with a topic during a session."""
        session = self._active_sessions.get(session_id)
        if not session:
            return False
        
        # Add topic to covered topics
        if topic_id not in session.topics_covered:
            session.topics_covered.append(topic_id)
        
        # Log specific interactions
        if interaction_type == "question":
            session.questions_asked += 1
            if success:
                session.questions_answered_correctly += 1
        elif interaction_type == "concept_explained":
            if topic_id not in session.concepts_explained:
                session.concepts_explained.append(topic_id)
        
        return True
    
    def update_topic_proficiency(self, user_id: str, topic_id: str, 
                               performance_data: Dict[str, Any]) -> bool:
        """Update topic proficiency based on performance data."""
        # Update base proficiency score
        score = performance_data.get("score", 0.0)
        assessment_type = performance_data.get("type", "interaction")
        
        success = self.profile_manager.update_proficiency_score(
            user_id, topic_id, score, assessment_type
        )
        
        if not success:
            return False
        
        # Update topic progress with detailed metrics
        updates = {
            "proficiency_score": score,
            "last_accessed": datetime.now()
        }
        
        # Add quiz scores if provided
        if "quiz_score" in performance_data:
            quiz_score = performance_data["quiz_score"]
            updates["quiz_scores"] = performance_data.get("quiz_scores", []) + [quiz_score]
        
        # Add mastery indicators
        if "mastery_indicators" in performance_data:
            updates["mastery_indicators"] = performance_data["mastery_indicators"]
        
        # Calculate completion percentage based on proficiency and interactions
        completion_pct = min(100.0, score * 100 + len(performance_data.get("interactions", [])) * 5)
        updates["completion_percentage"] = completion_pct
        
        self.profile_manager.update_topic_progress(user_id, topic_id, updates)
        
        # Update adaptive learning path
        self._update_adaptive_path(user_id, topic_id, performance_data)
        
        return True
    
    def get_progress_analytics(self, user_id: str, force_refresh: bool = False) -> Optional[ProgressAnalytics]:
        """Get comprehensive progress analytics for a user."""
        if user_id in self._analytics_cache and not force_refresh:
            return self._analytics_cache[user_id]
        
        profile = self.profile_manager.get_profile(user_id)
        if not profile:
            return None
        
        analytics = self._calculate_progress_analytics(profile)
        self._analytics_cache[user_id] = analytics
        
        # Save analytics to disk
        analytics_file = self.analytics_dir / f"{user_id}_analytics.json"
        with open(analytics_file, 'w', encoding='utf-8') as f:
            json.dump(analytics.model_dump(mode='json'), f, indent=2, default=str)
        
        return analytics
    
    def create_adaptive_learning_path(self, user_id: str, 
                                    path_type: LearningPathType = LearningPathType.ADAPTIVE) -> Optional[str]:
        """Create an adaptive learning path based on user analytics."""
        profile = self.profile_manager.get_profile(user_id)
        analytics = self.get_progress_analytics(user_id)
        
        if not profile or not analytics:
            return None
        
        # Create adaptive path
        adaptive_path = AdaptiveLearningPath(
            user_id=user_id,
            path_type=path_type,
            target_certification=profile.target_certification or CertificationLevel.FOUNDATION
        )
        
        # Generate initial topic recommendations
        adaptive_path.current_topics = self._generate_adaptive_topics(profile, analytics)
        adaptive_path.priority_topics = analytics.improvement_focus[:3]
        
        # Configure adaptation parameters based on user experience
        if profile.experience_level == ExperienceLevel.BEGINNER:
            adaptive_path.performance_threshold = 0.6
            adaptive_path.adaptation_sensitivity = 0.3
            adaptive_path.review_frequency = 2
        elif profile.experience_level == ExperienceLevel.EXPERT:
            adaptive_path.performance_threshold = 0.8
            adaptive_path.adaptation_sensitivity = 0.7
            adaptive_path.review_frequency = 5
        
        self._learning_paths[adaptive_path.path_id] = adaptive_path
        
        return adaptive_path.path_id
    
    def get_next_recommended_topics(self, user_id: str, count: int = 3) -> List[Dict[str, Any]]:
        """Get next recommended topics based on adaptive learning path."""
        profile = self.profile_manager.get_profile(user_id)
        analytics = self.get_progress_analytics(user_id)
        
        if not profile or not analytics:
            return []
        
        recommendations = []
        
        # Priority 1: Knowledge gaps that need immediate attention
        for topic_id in analytics.improvement_focus[:2]:
            gap_score = analytics.knowledge_gaps.get(topic_id, 0.0)
            recommendations.append({
                "topic_id": topic_id,
                "reason": "knowledge_gap",
                "priority": 1.0 - gap_score,
                "estimated_duration": self._estimate_topic_duration(topic_id, profile.experience_level),
                "difficulty": "review" if gap_score > 0.7 else "moderate"
            })
        
        # Priority 2: Next topics in structured plan (if active)
        if profile.active_plan_id:
            current_topic = self.profile_manager.get_current_topic(user_id)
            if current_topic:
                topic_data = current_topic["topic"]
                recommendations.append({
                    "topic_id": topic_data["topic_id"],
                    "reason": "structured_plan",
                    "priority": 0.8,
                    "estimated_duration": topic_data["estimated_duration_minutes"],
                    "difficulty": "planned"
                })
        
        # Priority 3: Adaptive suggestions based on performance
        for topic_id in analytics.suggested_next_topics:
            if topic_id not in [r["topic_id"] for r in recommendations]:
                recommendations.append({
                    "topic_id": topic_id,
                    "reason": "adaptive_suggestion",
                    "priority": 0.6,
                    "estimated_duration": self._estimate_topic_duration(topic_id, profile.experience_level),
                    "difficulty": "adaptive"
                })
        
        # Sort by priority and return top N
        recommendations.sort(key=lambda x: x["priority"], reverse=True)
        return recommendations[:count]
    
    def get_learning_insights(self, user_id: str) -> Dict[str, Any]:
        """Get personalized learning insights and recommendations."""
        analytics = self.get_progress_analytics(user_id)
        profile = self.profile_manager.get_profile(user_id)
        
        if not analytics or not profile:
            return {}
        
        insights = {
            "performance_summary": {
                "overall_progress": f"{analytics.overall_completion:.1f}%",
                "learning_velocity": self._interpret_learning_velocity(analytics.learning_velocity),
                "consistency": self._interpret_consistency(analytics.study_consistency),
                "retention": f"{analytics.retention_rate:.1%}"
            },
            "certification_readiness": {
                "foundation": {
                    "score": f"{analytics.foundation_readiness:.1%}",
                    "status": self._get_readiness_status(analytics.foundation_readiness),
                    "recommendation": self._get_certification_recommendation(
                        analytics.foundation_readiness, CertificationLevel.FOUNDATION
                    )
                }
            },
            "learning_optimization": {
                "optimal_session_length": f"{analytics.optimal_session_length} minutes",
                "best_study_times": analytics.peak_performance_times,
                "recommended_approach": self._get_approach_recommendation(profile, analytics)
            },
            "focus_areas": {
                "strengths": profile.strengths[:3],
                "improvement_needed": analytics.improvement_focus[:3],
                "next_priorities": [r["topic_id"] for r in self.get_next_recommended_topics(user_id, 3)]
            }
        }
        
        return insights
    
    def _calculate_progress_analytics(self, profile: UserProfile) -> ProgressAnalytics:
        """Calculate comprehensive progress analytics for a user."""
        analytics = ProgressAnalytics(user_id=profile.user_id)
        
        # Overall completion calculation
        if profile.topic_progress:
            total_completion = sum(tp.completion_percentage for tp in profile.topic_progress.values())
            analytics.overall_completion = total_completion / len(profile.topic_progress)
        
        # Study consistency (based on streak and session regularity)
        analytics.study_consistency = min(1.0, profile.streak_days / 30.0)  # 30-day streak = 1.0
        
        # Learning velocity (topics per hour)
        if profile.total_study_time_minutes > 0:
            study_hours = profile.total_study_time_minutes / 60.0
            topics_studied = len(profile.topic_progress)
            analytics.learning_velocity = topics_studied / study_hours if study_hours > 0 else 1.0
        
        # Retention rate (based on quiz performance over time)
        all_quiz_scores = []
        for tp in profile.topic_progress.values():
            all_quiz_scores.extend(tp.quiz_scores)
        
        if all_quiz_scores:
            analytics.retention_rate = sum(all_quiz_scores) / (len(all_quiz_scores) * 100.0)
        
        # Certification readiness
        foundation_topics = [tp for tp in profile.topic_progress.values() 
                           if tp.certification_level == CertificationLevel.FOUNDATION]
        if foundation_topics:
            foundation_avg = sum(tp.proficiency_score for tp in foundation_topics) / len(foundation_topics)
            analytics.foundation_readiness = foundation_avg
        
        # Knowledge gaps analysis
        analytics.knowledge_gaps = {
            tp.topic_id: 1.0 - tp.proficiency_score 
            for tp in profile.topic_progress.values() 
            if tp.proficiency_score < 0.7
        }
        
        # Improvement focus (topics with largest gaps)
        analytics.improvement_focus = sorted(
            analytics.knowledge_gaps.keys(),
            key=lambda k: analytics.knowledge_gaps[k],
            reverse=True
        )[:5]
        
        # Adaptive topic suggestions
        analytics.suggested_next_topics = self._generate_adaptive_topics(profile, analytics)
        
        # Peak performance times (placeholder - would analyze session times)
        analytics.peak_performance_times = profile.preferred_learning_times or ["morning"]
        
        # Optimal session length (based on average session duration and performance)
        if profile.average_session_duration_minutes > 0:
            analytics.optimal_session_length = int(profile.average_session_duration_minutes)
        else:
            analytics.optimal_session_length = profile.session_preferences.preferred_duration_minutes
        
        return analytics
    
    def _generate_adaptive_topics(self, profile: UserProfile, 
                                analytics: ProgressAnalytics) -> List[str]:
        """Generate adaptive topic suggestions based on user profile and analytics."""
        suggestions = []
        
        # Start with areas that need improvement
        suggestions.extend(analytics.improvement_focus[:2])
        
        # Add topics based on certification level and progress
        if profile.target_certification == CertificationLevel.FOUNDATION:
            foundation_topics = ["adm_overview", "preliminary_phase", "phase_a_vision", 
                               "business_architecture", "data_architecture"]
            
            # Filter out completed topics
            completed_topics = {tp.topic_id for tp in profile.topic_progress.values() 
                              if tp.status == TopicStatus.COMPLETED}
            
            for topic in foundation_topics:
                if topic not in completed_topics and topic not in suggestions:
                    suggestions.append(topic)
                    if len(suggestions) >= 5:
                        break
        
        return suggestions
    
    def _update_adaptive_path(self, user_id: str, topic_id: str, 
                            performance_data: Dict[str, Any]) -> None:
        """Update adaptive learning path based on topic performance."""
        # Find user's adaptive path
        user_path = None
        for path in self._learning_paths.values():
            if path.user_id == user_id:
                user_path = path
                break
        
        if not user_path:
            return
        
        # Update path based on performance
        score = performance_data.get("score", 0.0)
        
        if score >= user_path.performance_threshold:
            # Good performance - add topic to completed
            if topic_id not in user_path.completed_topics:
                user_path.completed_topics.append(topic_id)
            
            # Remove from current topics
            if topic_id in user_path.current_topics:
                user_path.current_topics.remove(topic_id)
        else:
            # Poor performance - add to priority topics for review
            if topic_id not in user_path.priority_topics:
                user_path.priority_topics.append(topic_id)
        
        user_path.last_updated = datetime.now()
    
    def _calculate_engagement_score(self, session: LearningSession) -> float:
        """Calculate engagement score based on session activity."""
        base_score = 0.5
        
        # Questions asked contribute to engagement
        if session.questions_asked > 0:
            base_score += min(0.3, session.questions_asked * 0.1)
        
        # Topics covered
        if session.topics_covered:
            base_score += min(0.2, len(session.topics_covered) * 0.05)
        
        return min(1.0, base_score)
    
    def _calculate_comprehension_score(self, session: LearningSession) -> float:
        """Calculate comprehension score based on session performance."""
        if session.questions_asked == 0:
            return 0.7  # Default for sessions without questions
        
        accuracy = session.questions_answered_correctly / session.questions_asked
        return accuracy
    
    def _save_session(self, session: LearningSession) -> None:
        """Save session data to disk."""
        session_file = self.sessions_dir / f"{session.session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session.model_dump(mode='json'), f, indent=2, default=str)
    
    def _update_user_analytics(self, user_id: str) -> None:
        """Update user analytics after session completion."""
        # Force refresh of analytics cache
        self.get_progress_analytics(user_id, force_refresh=True)
    
    def _estimate_topic_duration(self, topic_id: str, experience_level: ExperienceLevel) -> int:
        """Estimate duration for a topic based on user experience level."""
        base_duration = 45  # minutes
        
        multipliers = {
            ExperienceLevel.BEGINNER: 1.3,
            ExperienceLevel.INTERMEDIATE: 1.0,
            ExperienceLevel.ADVANCED: 0.8,
            ExperienceLevel.EXPERT: 0.6
        }
        
        return int(base_duration * multipliers.get(experience_level, 1.0))
    
    def _interpret_learning_velocity(self, velocity: float) -> str:
        """Interpret learning velocity score into human-readable format."""
        if velocity >= 2.0:
            return "Very Fast"
        elif velocity >= 1.5:
            return "Fast"
        elif velocity >= 1.0:
            return "Moderate"
        elif velocity >= 0.5:
            return "Steady"
        else:
            return "Slow"
    
    def _interpret_consistency(self, consistency: float) -> str:
        """Interpret consistency score into human-readable format."""
        if consistency >= 0.8:
            return "Excellent"
        elif consistency >= 0.6:
            return "Good"
        elif consistency >= 0.4:
            return "Fair"
        else:
            return "Needs Improvement"
    
    def _get_readiness_status(self, readiness_score: float) -> str:
        """Get certification readiness status."""
        if readiness_score >= 0.85:
            return "Ready"
        elif readiness_score >= 0.7:
            return "Almost Ready"
        elif readiness_score >= 0.5:
            return "Needs More Study"
        else:
            return "Not Ready"
    
    def _get_certification_recommendation(self, readiness_score: float, 
                                        cert_level: CertificationLevel) -> str:
        """Get certification recommendation based on readiness."""
        if readiness_score >= 0.85:
            return "You're ready to take the exam! Schedule it soon."
        elif readiness_score >= 0.7:
            return "Review weak areas and take a few practice exams."
        elif readiness_score >= 0.5:
            return "Continue studying and focus on improvement areas."
        else:
            return "Build stronger foundation before attempting the exam."
    
    def _get_approach_recommendation(self, profile: UserProfile, 
                                   analytics: ProgressAnalytics) -> str:
        """Get learning approach recommendation."""
        if analytics.study_consistency < 0.5:
            return "Focus on building a consistent daily study habit"
        elif len(analytics.knowledge_gaps) > 5:
            return "Review fundamentals before advancing to new topics"
        elif analytics.learning_velocity < 0.5:
            return "Consider shorter, more frequent study sessions"
        else:
            return "Continue with your current approach - it's working well!"