"""
Enhanced user profile data models and management system for TOGAF Agent.
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..knowledge_base.metadata_schema import CertificationLevel


class ExperienceLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class LearningApproach(str, Enum):
    STRUCTURED = "structured"
    ADHOC = "adhoc"
    HYBRID = "hybrid"


class SessionIntensity(str, Enum):
    LIGHT = "light"
    MODERATE = "moderate"
    INTENSIVE = "intensive"


class LearningStyle(str, Enum):
    VISUAL = "visual"
    READING_WRITING = "reading_writing"


class TopicStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class PlanType(str, Enum):
    FOUNDATION_BEGINNER = "foundation_beginner"
    FOUNDATION_REVIEW = "foundation_review"
    PRACTITIONER_PREP = "practitioner_prep"
    EXTENDED_PRACTITIONER = "extended_practitioner"
    CUSTOM_TOPICS = "custom_topics"
    EXAM_FOCUSED = "exam_focused"


class LearningPlanTopic(BaseModel):
    topic_id: str
    title: str
    description: str
    certification_level: CertificationLevel
    estimated_duration_minutes: int
    prerequisites: List[str] = Field(default_factory=list)  # topic_ids that should be completed first
    is_optional: bool = False
    order_index: int
    status: TopicStatus = TopicStatus.NOT_STARTED
    completion_date: Optional[datetime] = None
    user_marked_complete: bool = False  # User manually marked as complete
    auto_completion_criteria: Dict[str, Any] = Field(default_factory=dict)


class StructuredLearningPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    plan_name: str
    plan_type: PlanType
    description: str
    target_certification: CertificationLevel
    created_date: datetime = Field(default_factory=datetime.now)
    estimated_total_duration_minutes: int
    
    # Plan structure
    topics: List[LearningPlanTopic] = Field(default_factory=list)
    current_topic_index: int = 0
    
    # Progress tracking
    is_active: bool = True
    completion_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    topics_completed: int = 0
    total_time_spent_minutes: int = 0
    
    # Plan preferences
    allow_topic_skipping: bool = True
    enforce_prerequisites: bool = True
    auto_advance: bool = False  # Automatically move to next topic when current is completed


class LearningGoal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    certification_level: CertificationLevel
    target_completion_date: Optional[datetime] = None
    priority: int = Field(default=1, ge=1, le=5)
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    associated_plan_id: Optional[str] = None  # Link to structured learning plan


class TopicProgress(BaseModel):
    topic_id: str
    certification_level: CertificationLevel
    experience_level: ExperienceLevel = ExperienceLevel.BEGINNER
    completion_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    proficiency_score: float = Field(default=0.0, ge=0.0, le=1.0)
    time_spent_minutes: int = Field(default=0, ge=0)
    last_accessed: Optional[datetime] = None
    quiz_scores: List[float] = Field(default_factory=list)
    exam_question_scores: List[Dict[str, Any]] = Field(default_factory=list)
    notes: str = ""
    mastery_indicators: Dict[str, bool] = Field(default_factory=dict)
    
    # Structured plan integration
    is_part_of_plan: bool = False
    plan_id: Optional[str] = None
    status: TopicStatus = TopicStatus.NOT_STARTED
    marked_complete_by_user: bool = False
    completion_date: Optional[datetime] = None


class ConversationPreferences(BaseModel):
    learning_style: LearningStyle = LearningStyle.READING_WRITING
    explanation_depth: str = Field(default="moderate", pattern="^(brief|moderate|detailed)$")
    use_examples: bool = True
    use_diagrams: bool = True
    interactive_mode: bool = True
    question_difficulty: str = Field(default="adaptive", pattern="^(easy|moderate|hard|adaptive)$")
    preferred_response_length: str = Field(default="moderate", pattern="^(concise|moderate|detailed)$")


class SessionPreferences(BaseModel):
    preferred_duration_minutes: int = Field(default=30, ge=15, le=120)
    session_intensity: SessionIntensity = SessionIntensity.MODERATE
    break_frequency_minutes: int = Field(default=20, ge=10, le=60)
    reminder_notifications: bool = True
    progress_tracking: bool = True


class UserProfile(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    last_active: datetime = Field(default_factory=datetime.now)
    
    # Core proficiency assessment
    experience_level: ExperienceLevel = ExperienceLevel.BEGINNER
    proficiency_scores: Dict[str, float] = Field(default_factory=dict)  # topic_id -> score (0-1)
    overall_proficiency: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Learning preferences and approach
    learning_approach: LearningApproach = LearningApproach.HYBRID
    structured_weight: float = Field(default=0.7, ge=0.0, le=1.0)  # Balance for hybrid approach
    
    # Certification focus
    exam_preparation_mode: bool = False
    target_certification: Optional[CertificationLevel] = None
    exam_readiness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    certification_deadline: Optional[datetime] = None
    
    # Structured Learning Plans
    learning_plans: Dict[str, StructuredLearningPlan] = Field(default_factory=dict)  # plan_id -> plan
    active_plan_id: Optional[str] = None
    
    # Learning context and goals
    learning_goals: List[LearningGoal] = Field(default_factory=list)
    topic_progress: Dict[str, TopicProgress] = Field(default_factory=dict)
    conversation_preferences: ConversationPreferences = Field(default_factory=ConversationPreferences)
    session_preferences: SessionPreferences = Field(default_factory=SessionPreferences)
    
    # Performance tracking and analytics
    total_study_time_minutes: int = Field(default=0, ge=0)
    sessions_completed: int = Field(default=0, ge=0)
    average_session_duration_minutes: float = Field(default=0.0, ge=0.0)
    streak_days: int = Field(default=0, ge=0)
    last_study_date: Optional[datetime] = None
    
    # Adaptive learning insights
    strengths: List[str] = Field(default_factory=list)
    areas_for_improvement: List[str] = Field(default_factory=list)
    learning_velocity: float = Field(default=1.0, ge=0.1, le=5.0)  # Learning speed multiplier
    retention_score: float = Field(default=0.0, ge=0.0, le=1.0)
    preferred_learning_times: List[str] = Field(default_factory=list)  # ["morning", "afternoon", "evening"]
    
    # Knowledge gap analysis
    knowledge_gaps: Dict[str, float] = Field(default_factory=dict)  # topic_id -> gap_score (0-1)
    last_assessment_date: Optional[datetime] = None
    assessment_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Session and conversation context
    current_session_id: Optional[str] = None
    current_topic_focus: Optional[str] = None
    
    # Metadata and customization
    profile_version: str = "2.0"
    custom_tags: List[str] = Field(default_factory=list)
    onboarding_completed: bool = False
    last_onboarding_step: str = ""
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserProfileManager:
    """Enhanced user profile manager with structured learning plan support."""
    
    def __init__(self, profiles_dir: Path = Path("./user_data/user_profiles")):
        self.profiles_dir = profiles_dir
        self.profiles_dir.mkdir(exist_ok=True)
        self._profiles_cache: Dict[str, UserProfile] = {}
        
        # Predefined plan templates
        self.plan_templates = {
            PlanType.FOUNDATION_BEGINNER: self._create_foundation_beginner_template(),
            PlanType.FOUNDATION_REVIEW: self._create_foundation_review_template(),
            PlanType.PRACTITIONER_PREP: self._create_practitioner_prep_template(),
            PlanType.EXTENDED_PRACTITIONER: self._create_extended_practitioner_template()
        }
    
    def create_profile(self, username: str, email: Optional[str] = None) -> UserProfile:
        """Create a new user profile with default settings."""
        if self.get_profile_by_username(username):
            raise ValueError(f"User '{username}' already exists")
        
        profile = UserProfile(username=username, email=email)
        self.save_profile(profile)
        return profile
    
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID with caching."""
        if user_id in self._profiles_cache:
            return self._profiles_cache[user_id]
        
        profile_file = self.profiles_dir / f"{user_id}.json"
        if not profile_file.exists():
            return None
        
        with open(profile_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        profile = UserProfile.model_validate(data)
        self._profiles_cache[user_id] = profile
        return profile
    
    def get_profile_by_username(self, username: str) -> Optional[UserProfile]:
        """Get user profile by username."""
        for profile_file in self.profiles_dir.glob("*.json"):
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if data.get('username') == username:
                    profile = UserProfile.model_validate(data)
                    self._profiles_cache[profile.user_id] = profile
                    return profile
            except (json.JSONDecodeError, ValueError):
                continue
        return None
    
    def save_profile(self, profile: UserProfile) -> None:
        """Save user profile to disk with updated activity timestamp."""
        profile.last_active = datetime.now()
        profile_file = self.profiles_dir / f"{profile.user_id}.json"
        
        with open(profile_file, 'w', encoding='utf-8') as f:
            json.dump(profile.model_dump(mode='json'), f, indent=2, default=str)
        
        self._profiles_cache[profile.user_id] = profile
    
    def create_structured_plan(self, user_id: str, plan_type: PlanType, 
                             custom_topics: Optional[List[str]] = None,
                             plan_name: Optional[str] = None) -> Optional[str]:
        """Create a structured learning plan for the user."""
        profile = self.get_profile(user_id)
        if not profile:
            return None
        
        if plan_type == PlanType.CUSTOM_TOPICS and custom_topics:
            plan = self._create_custom_plan(custom_topics, plan_name or "Custom Learning Plan")
        else:
            template = self.plan_templates.get(plan_type)
            if not template:
                return None
            plan = template.model_copy(deep=True)
            plan.plan_id = str(uuid.uuid4())
        
        # Adjust plan based on user experience level
        self._adjust_plan_for_experience(plan, profile.experience_level)
        
        # Add plan to user profile
        profile.learning_plans[plan.plan_id] = plan
        
        # Set as active plan if user doesn't have one
        if not profile.active_plan_id:
            profile.active_plan_id = plan.plan_id
        
        self.save_profile(profile)
        return plan.plan_id
    
    def mark_topic_complete(self, user_id: str, topic_id: str, 
                          user_initiated: bool = True) -> bool:
        """Mark a topic as completed in user's active learning plan."""
        profile = self.get_profile(user_id)
        if not profile or not profile.active_plan_id:
            return False
        
        active_plan = profile.learning_plans.get(profile.active_plan_id)
        if not active_plan:
            return False
        
        # Find and update topic in plan
        topic_updated = False
        for topic in active_plan.topics:
            if topic.topic_id == topic_id:
                topic.status = TopicStatus.COMPLETED
                topic.completion_date = datetime.now()
                topic.user_marked_complete = user_initiated
                topic_updated = True
                break
        
        if not topic_updated:
            return False
        
        # Update topic progress
        if topic_id not in profile.topic_progress:
            profile.topic_progress[topic_id] = TopicProgress(
                topic_id=topic_id,
                certification_level=active_plan.target_certification
            )
        
        topic_progress = profile.topic_progress[topic_id]
        topic_progress.status = TopicStatus.COMPLETED
        topic_progress.marked_complete_by_user = user_initiated
        topic_progress.completion_date = datetime.now()
        topic_progress.completion_percentage = 100.0
        topic_progress.is_part_of_plan = True
        topic_progress.plan_id = active_plan.plan_id
        
        # Update plan progress
        self._update_plan_progress(active_plan)
        
        # Auto-advance to next topic if enabled
        if active_plan.auto_advance:
            self._advance_to_next_topic(active_plan)
        
        self.save_profile(profile)
        return True
    
    def skip_topic(self, user_id: str, topic_id: str) -> bool:
        """Skip a topic in user's active learning plan."""
        profile = self.get_profile(user_id)
        if not profile or not profile.active_plan_id:
            return False
        
        active_plan = profile.learning_plans.get(profile.active_plan_id)
        if not active_plan or not active_plan.allow_topic_skipping:
            return False
        
        # Find and update topic in plan
        for topic in active_plan.topics:
            if topic.topic_id == topic_id:
                topic.status = TopicStatus.SKIPPED
                break
        else:
            return False
        
        # Update topic progress
        if topic_id not in profile.topic_progress:
            profile.topic_progress[topic_id] = TopicProgress(
                topic_id=topic_id,
                certification_level=active_plan.target_certification
            )
        
        topic_progress = profile.topic_progress[topic_id]
        topic_progress.status = TopicStatus.SKIPPED
        topic_progress.is_part_of_plan = True
        topic_progress.plan_id = active_plan.plan_id
        
        # Update plan progress and advance
        self._update_plan_progress(active_plan)
        self._advance_to_next_topic(active_plan)
        
        self.save_profile(profile)
        return True
    
    def get_current_topic(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the current topic in user's active learning plan."""
        profile = self.get_profile(user_id)
        if not profile or not profile.active_plan_id:
            return None
        
        active_plan = profile.learning_plans.get(profile.active_plan_id)
        if not active_plan or active_plan.current_topic_index >= len(active_plan.topics):
            return None
        
        current_topic = active_plan.topics[active_plan.current_topic_index]
        
        return {
            "topic": current_topic.model_dump(),
            "plan_progress": {
                "current_index": active_plan.current_topic_index,
                "total_topics": len(active_plan.topics),
                "completion_percentage": active_plan.completion_percentage
            },
            "can_proceed": self._can_proceed_to_topic(active_plan, current_topic),
            "next_available_topics": self._get_next_available_topics(active_plan)
        }
    
    def get_plan_overview(self, user_id: str, plan_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get overview of user's learning plan."""
        profile = self.get_profile(user_id)
        if not profile:
            return None
        
        target_plan_id = plan_id or profile.active_plan_id
        if not target_plan_id or target_plan_id not in profile.learning_plans:
            return None
        
        plan = profile.learning_plans[target_plan_id]
        
        # Categorize topics by status
        topics_by_status = {
            "completed": [],
            "in_progress": [],
            "available": [],
            "locked": [],
            "skipped": []
        }
        
        for i, topic in enumerate(plan.topics):
            if topic.status == TopicStatus.COMPLETED:
                topics_by_status["completed"].append(topic)
            elif topic.status == TopicStatus.SKIPPED:
                topics_by_status["skipped"].append(topic)
            elif topic.status == TopicStatus.IN_PROGRESS:
                topics_by_status["in_progress"].append(topic)
            elif i == plan.current_topic_index and topic.status == TopicStatus.NOT_STARTED:
                # Current topic that hasn't been explicitly marked should be considered "in progress"
                topics_by_status["in_progress"].append(topic)
            elif self._can_proceed_to_topic(plan, topic):
                topics_by_status["available"].append(topic)
            else:
                topics_by_status["locked"].append(topic)
        
        return {
            "plan": plan.model_dump(),
            "topics_by_status": {k: [t.model_dump() for t in v] for k, v in topics_by_status.items()},
            "progress_summary": {
                "completion_percentage": plan.completion_percentage,
                "topics_completed": plan.topics_completed,
                "total_topics": len(plan.topics),
                "estimated_time_remaining": self._calculate_remaining_time(plan),
                "current_topic_index": plan.current_topic_index
            }
        }
    
    def _create_foundation_beginner_template(self) -> StructuredLearningPlan:
        """Create Foundation level beginner learning plan template."""
        topics = [
            LearningPlanTopic(
                topic_id="togaf_introduction",
                title="Introduction to TOGAF",
                description="Overview of enterprise architecture and TOGAF framework",
                certification_level=CertificationLevel.FOUNDATION,
                estimated_duration_minutes=45,
                order_index=0
            ),
            LearningPlanTopic(
                topic_id="enterprise_architecture_concepts",
                title="Enterprise Architecture Core Concepts",
                description="Fundamental EA concepts and terminology",
                certification_level=CertificationLevel.FOUNDATION,
                estimated_duration_minutes=60,
                order_index=1,
                prerequisites=["togaf_introduction"]
            ),
            LearningPlanTopic(
                topic_id="adm_overview",
                title="Architecture Development Method (ADM) Overview",
                description="Introduction to TOGAF ADM phases and approach",
                certification_level=CertificationLevel.FOUNDATION,
                estimated_duration_minutes=90,
                order_index=2,
                prerequisites=["enterprise_architecture_concepts"]
            ),
            LearningPlanTopic(
                topic_id="preliminary_phase",
                title="Preliminary Phase",
                description="Preparing for architecture work",
                certification_level=CertificationLevel.FOUNDATION,
                estimated_duration_minutes=75,
                order_index=3,
                prerequisites=["adm_overview"]
            ),
            LearningPlanTopic(
                topic_id="phase_a_vision",
                title="Phase A: Architecture Vision",
                description="Creating and validating architecture vision",
                certification_level=CertificationLevel.FOUNDATION,
                estimated_duration_minutes=90,
                order_index=4,
                prerequisites=["preliminary_phase"]
            )
        ]
        
        total_duration = sum(topic.estimated_duration_minutes for topic in topics)
        
        return StructuredLearningPlan(
            plan_name="TOGAF Foundation for Beginners",
            plan_type=PlanType.FOUNDATION_BEGINNER,
            description="Structured learning path for TOGAF Foundation certification - beginner level",
            target_certification=CertificationLevel.FOUNDATION,
            topics=topics,
            estimated_total_duration_minutes=total_duration,
            allow_topic_skipping=True,
            enforce_prerequisites=True
        )
    
    def _create_foundation_review_template(self) -> StructuredLearningPlan:
        """Create Foundation level review learning plan template."""
        topics = [
            LearningPlanTopic(
                topic_id="part_0_introduction_core_concepts",
                title="Introduction and Core Concepts",
                description="TOGAF framework overview and fundamental enterprise architecture concepts",
                certification_level=CertificationLevel.FOUNDATION,
                estimated_duration_minutes=45,
                order_index=0
            ),
            LearningPlanTopic(
                topic_id="part_1_architecture_development_method",
                title="Architecture Development Method",
                description="Complete ADM lifecycle and phase-by-phase approach",
                certification_level=CertificationLevel.FOUNDATION,
                estimated_duration_minutes=60,
                order_index=1
            ),
            LearningPlanTopic(
                topic_id="part_2_adm_techniques",
                title="ADM Techniques",
                description="Key techniques, guidelines, and best practices for ADM phases",
                certification_level=CertificationLevel.FOUNDATION,
                estimated_duration_minutes=50,
                order_index=2
            ),
            LearningPlanTopic(
                topic_id="part_3_applying_adm",
                title="Applying the ADM",
                description="Practical application of ADM in different contexts and scenarios",
                certification_level=CertificationLevel.FOUNDATION,
                estimated_duration_minutes=45,
                order_index=3
            ),
            LearningPlanTopic(
                topic_id="part_4_architecture_content",
                title="Architecture Content",
                description="Architecture artifacts, deliverables, and enterprise continuum",
                certification_level=CertificationLevel.FOUNDATION,
                estimated_duration_minutes=50,
                order_index=4
            ),
            LearningPlanTopic(
                topic_id="part_5_enterprise_capability_governance",
                title="Enterprise Architecture Capability & Governance",
                description="Architecture governance, capability management, and organizational structures",
                certification_level=CertificationLevel.FOUNDATION,
                estimated_duration_minutes=50,
                order_index=5
            )
        ]
        
        total_duration = sum(topic.estimated_duration_minutes for topic in topics)
        
        return StructuredLearningPlan(
            plan_name="TOGAF Foundation Review",
            plan_type=PlanType.FOUNDATION_REVIEW,
            description="Quick review of key TOGAF Foundation concepts",
            target_certification=CertificationLevel.FOUNDATION,
            topics=topics,
            estimated_total_duration_minutes=total_duration,
            allow_topic_skipping=True,
            enforce_prerequisites=False
        )
    
    def _create_practitioner_prep_template(self) -> StructuredLearningPlan:
        """Create Practitioner level preparation learning plan template."""
        topics = [
            LearningPlanTopic(
                topic_id="practitioners_approach_adm",
                title="Practitioner's Approach to ADM",
                description="Practical guidance for implementing the Architecture Development Method",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=90,
                order_index=0
            ),
            LearningPlanTopic(
                topic_id="business_capabilities",
                title="Business Capabilities",
                description="Business capability modeling and management techniques",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=75,
                order_index=1
            ),
            LearningPlanTopic(
                topic_id="risk_security_integration",
                title="Risk and Security Integration",
                description="Integrating risk management and security into enterprise architecture",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=80,
                order_index=2
            ),
            LearningPlanTopic(
                topic_id="digital_enterprise",
                title="Digital Enterprise Architecture",
                description="Architecture approaches for digital transformation and modern enterprises",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=85,
                order_index=3
            ),
            LearningPlanTopic(
                topic_id="value_streams",
                title="Value Streams and Value Stream Mapping",
                description="Value stream identification, mapping, and optimization techniques",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=70,
                order_index=4
            ),
            LearningPlanTopic(
                topic_id="business_scenarios",
                title="Business Scenarios",
                description="Using business scenarios to drive architecture requirements",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=65,
                order_index=5
            ),
            LearningPlanTopic(
                topic_id="ea_capability_guide",
                title="Enterprise Architecture Capability",
                description="Building and managing enterprise architecture capability",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=80,
                order_index=6
            ),
            LearningPlanTopic(
                topic_id="architecture_maturity_models",
                title="Architecture Maturity Models",
                description="Assessing and improving architecture maturity in organizations",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=75,
                order_index=7
            )
        ]
        
        total_duration = sum(topic.estimated_duration_minutes for topic in topics)
        
        return StructuredLearningPlan(
            plan_name="TOGAF Practitioner Preparation",
            plan_type=PlanType.PRACTITIONER_PREP,
            description="Advanced topics for TOGAF Practitioner certification",
            target_certification=CertificationLevel.PRACTITIONER,
            topics=topics,
            estimated_total_duration_minutes=total_duration,
            allow_topic_skipping=False,
            enforce_prerequisites=True
        )
    
    def _create_extended_practitioner_template(self) -> StructuredLearningPlan:
        """Create Extended Practitioner Guides learning plan template."""
        topics = [
            LearningPlanTopic(
                topic_id="information_mapping",
                title="Information Mapping",
                description="Advanced techniques for mapping and managing enterprise information",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=70,
                order_index=0
            ),
            LearningPlanTopic(
                topic_id="enterprise_agility",
                title="Enterprise Agility",
                description="Architecture approaches for achieving organizational agility",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=75,
                order_index=1
            ),
            LearningPlanTopic(
                topic_id="business_models",
                title="Business Models in Enterprise Architecture",
                description="Modeling and analyzing business models within EA framework",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=65,
                order_index=2
            ),
            LearningPlanTopic(
                topic_id="adm_agile_sprints",
                title="ADM with Agile Development Sprints",
                description="Integrating TOGAF ADM with agile development methodologies",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=80,
                order_index=3
            ),
            LearningPlanTopic(
                topic_id="organization_mapping",
                title="Organization Mapping",
                description="Mapping organizational structures and relationships in EA",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=60,
                order_index=4
            ),
            LearningPlanTopic(
                topic_id="soa_guide",
                title="Service-Oriented Architecture (SOA)",
                description="SOA principles and implementation within TOGAF framework",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=85,
                order_index=5
            ),
            LearningPlanTopic(
                topic_id="trm_guide",
                title="Technical Reference Model (TRM)",
                description="Understanding and applying the TOGAF Technical Reference Model",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=70,
                order_index=6
            ),
            LearningPlanTopic(
                topic_id="iii_rm_guide",
                title="Integrated Information Infrastructure Reference Model",
                description="III-RM for information systems architecture planning",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=75,
                order_index=7
            ),
            LearningPlanTopic(
                topic_id="digital_technology_adoption",
                title="Digital Technology Adoption",
                description="Strategies for adopting and integrating digital technologies",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=80,
                order_index=8
            ),
            LearningPlanTopic(
                topic_id="microservices_architecture",
                title="Microservices Architecture",
                description="Microservices patterns and principles in enterprise architecture",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=90,
                order_index=9
            ),
            LearningPlanTopic(
                topic_id="government_reference_model",
                title="Government Reference Model",
                description="TOGAF adaptation for government and public sector organizations",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=65,
                order_index=10
            ),
            LearningPlanTopic(
                topic_id="architecture_skills_framework",
                title="Architecture Skills Framework",
                description="Building and managing architecture team capabilities",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=60,
                order_index=11
            ),
            LearningPlanTopic(
                topic_id="business_capability_planning",
                title="Business Capability Planning",
                description="Advanced business capability planning and roadmapping",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=70,
                order_index=12
            ),
            LearningPlanTopic(
                topic_id="digital_business_reference_model",
                title="Digital Business Reference Model",
                description="Reference models for digital business transformation",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=75,
                order_index=13
            ),
            LearningPlanTopic(
                topic_id="information_arch_metadata",
                title="Information Architecture and Metadata",
                description="Advanced information architecture and metadata management",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=65,
                order_index=14
            ),
            LearningPlanTopic(
                topic_id="bi_analytics",
                title="Business Intelligence and Analytics",
                description="BI and analytics architecture within enterprise context",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=80,
                order_index=15
            ),
            LearningPlanTopic(
                topic_id="sustainable_is",
                title="Sustainable Information Systems",
                description="Green IT and sustainable information systems architecture",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=60,
                order_index=16
            ),
            LearningPlanTopic(
                topic_id="customer_mdm",
                title="Customer Master Data Management",
                description="Customer MDM strategies and implementation approaches",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=70,
                order_index=17
            ),
            LearningPlanTopic(
                topic_id="architecture_project_management",
                title="Architecture Project Management",
                description="Managing architecture projects and transformation initiatives",
                certification_level=CertificationLevel.PRACTITIONER,
                estimated_duration_minutes=85,
                order_index=18
            )
        ]
        
        total_duration = sum(topic.estimated_duration_minutes for topic in topics)
        
        return StructuredLearningPlan(
            plan_name="Extended Practitioner Guides",
            plan_type=PlanType.EXTENDED_PRACTITIONER,
            description="Comprehensive coverage of specialized TOGAF Practitioner guides and advanced topics",
            target_certification=CertificationLevel.PRACTITIONER,
            topics=topics,
            estimated_total_duration_minutes=total_duration,
            allow_topic_skipping=True,
            enforce_prerequisites=False,
            auto_advance=False
        )
    
    def _create_custom_plan(self, topics: List[str], plan_name: str) -> StructuredLearningPlan:
        """Create a custom learning plan with specified topics."""
        plan_topics = []
        for i, topic_id in enumerate(topics):
            plan_topics.append(
                LearningPlanTopic(
                    topic_id=topic_id,
                    title=topic_id.replace("_", " ").title(),
                    description=f"Custom topic: {topic_id}",
                    certification_level=CertificationLevel.FOUNDATION,
                    estimated_duration_minutes=60,
                    order_index=i
                )
            )
        
        return StructuredLearningPlan(
            plan_name=plan_name,
            plan_type=PlanType.CUSTOM_TOPICS,
            description="Custom learning plan based on user-selected topics",
            target_certification=CertificationLevel.FOUNDATION,
            topics=plan_topics,
            estimated_total_duration_minutes=len(topics) * 60,
            allow_topic_skipping=True,
            enforce_prerequisites=False
        )
    
    def _adjust_plan_for_experience(self, plan: StructuredLearningPlan, 
                                  experience_level: ExperienceLevel) -> None:
        """Adjust plan difficulty and pacing based on user experience."""
        if experience_level == ExperienceLevel.BEGINNER:
            # Add more time for each topic
            for topic in plan.topics:
                topic.estimated_duration_minutes = int(topic.estimated_duration_minutes * 1.2)
        elif experience_level in [ExperienceLevel.ADVANCED, ExperienceLevel.EXPERT]:
            # Reduce time and allow skipping
            for topic in plan.topics:
                topic.estimated_duration_minutes = int(topic.estimated_duration_minutes * 0.8)
            plan.allow_topic_skipping = True
            plan.enforce_prerequisites = False
    
    def _can_proceed_to_topic(self, plan: StructuredLearningPlan, 
                            topic: LearningPlanTopic) -> bool:
        """Check if user can proceed to a specific topic based on prerequisites."""
        if not plan.enforce_prerequisites:
            return True
        
        # Check if all prerequisites are completed
        for prereq_id in topic.prerequisites:
            prereq_topic = next((t for t in plan.topics if t.topic_id == prereq_id), None)
            if not prereq_topic or prereq_topic.status != TopicStatus.COMPLETED:
                return False
        
        return True
    
    def _get_next_available_topics(self, plan: StructuredLearningPlan) -> List[LearningPlanTopic]:
        """Get list of topics that are available to study next."""
        available_topics = []
        
        for topic in plan.topics:
            if (topic.status == TopicStatus.NOT_STARTED and 
                self._can_proceed_to_topic(plan, topic)):
                available_topics.append(topic)
        
        return available_topics[:3]  # Return up to 3 next available topics
    
    def _update_plan_progress(self, plan: StructuredLearningPlan) -> None:
        """Update overall plan progress statistics."""
        completed_topics = [t for t in plan.topics if t.status == TopicStatus.COMPLETED]
        plan.topics_completed = len(completed_topics)
        plan.completion_percentage = (len(completed_topics) / len(plan.topics)) * 100 if plan.topics else 0
    
    def _advance_to_next_topic(self, plan: StructuredLearningPlan) -> None:
        """Advance current topic index to next available topic."""
        for i in range(plan.current_topic_index + 1, len(plan.topics)):
            topic = plan.topics[i]
            if (topic.status == TopicStatus.NOT_STARTED and 
                self._can_proceed_to_topic(plan, topic)):
                plan.current_topic_index = i
                break
    
    def _calculate_remaining_time(self, plan: StructuredLearningPlan) -> int:
        """Calculate estimated remaining time for plan completion."""
        remaining_topics = [t for t in plan.topics 
                          if t.status not in [TopicStatus.COMPLETED, TopicStatus.SKIPPED]]
        return sum(topic.estimated_duration_minutes for topic in remaining_topics)
    
    # ... (keeping all other existing methods for compatibility)
    def update_proficiency_score(self, user_id: str, topic_id: str, 
                               score: float, assessment_type: str = "general") -> bool:
        """Update proficiency score for a specific topic."""
        profile = self.get_profile(user_id)
        if not profile:
            return False
        
        profile.proficiency_scores[topic_id] = max(0.0, min(1.0, score))
        
        if profile.proficiency_scores:
            profile.overall_proficiency = sum(profile.proficiency_scores.values()) / len(profile.proficiency_scores)
        
        if profile.overall_proficiency >= 0.8:
            profile.experience_level = ExperienceLevel.EXPERT
        elif profile.overall_proficiency >= 0.6:
            profile.experience_level = ExperienceLevel.ADVANCED
        elif profile.overall_proficiency >= 0.4:
            profile.experience_level = ExperienceLevel.INTERMEDIATE
        else:
            profile.experience_level = ExperienceLevel.BEGINNER
        
        assessment_record = {
            "timestamp": datetime.now().isoformat(),
            "topic_id": topic_id,
            "score": score,
            "assessment_type": assessment_type,
            "overall_proficiency": profile.overall_proficiency
        }
        profile.assessment_history.append(assessment_record)
        
        self.save_profile(profile)
        return True
    
    def list_all_profiles(self) -> List[UserProfile]:
        """List all user profiles sorted by last activity."""
        profiles = []
        for profile_file in self.profiles_dir.glob("*.json"):
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                profile = UserProfile.model_validate(data)
                profiles.append(profile)
            except (json.JSONDecodeError, ValueError):
                continue
        
        return sorted(profiles, key=lambda p: p.last_active, reverse=True)
    
    def delete_profile(self, user_id: str) -> bool:
        """Delete a user profile and clear cache."""
        profile_file = self.profiles_dir / f"{user_id}.json"
        if profile_file.exists():
            profile_file.unlink()
            self._profiles_cache.pop(user_id, None)
            return True
        return False
    
    def get_user_statistics(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive user statistics."""
        profile = self.get_profile(user_id)
        if not profile:
            return None
        
        # Get active learning plan
        active_plan = None
        if profile.active_plan_id and profile.active_plan_id in profile.learning_plans:
            active_plan = profile.learning_plans[profile.active_plan_id]
        
        # Calculate topics studied
        topics_studied = len([topic for topic in (active_plan.topics if active_plan else []) 
                            if topic.status in [TopicStatus.COMPLETED, TopicStatus.IN_PROGRESS]])
        
        # Calculate current streak (simplified - would need session data for real streak)
        current_streak = 0
        if profile.last_study_date:
            from datetime import datetime
            today = datetime.now().date()
            last_study = profile.last_study_date.date() if hasattr(profile.last_study_date, 'date') else profile.last_study_date
            if isinstance(last_study, str):
                try:
                    last_study = datetime.fromisoformat(last_study.replace('Z', '+00:00')).date()
                except:
                    last_study = today
            
            if (today - last_study).days <= 1:
                current_streak = profile.streak_days
        
        return {
            "profile": {
                "user_id": profile.user_id,
                "username": profile.username,
                "experience_level": profile.experience_level.value,
                "overall_proficiency": profile.overall_proficiency,
                "target_certification": profile.target_certification.value if profile.target_certification else None,
                "onboarding_completed": profile.onboarding_completed
            },
            "activity": {
                "total_sessions": profile.sessions_completed,
                "total_study_time": profile.total_study_time_minutes,
                "average_session_duration": profile.average_session_duration_minutes,
                "current_streak": current_streak,
                "last_study_date": profile.last_study_date.isoformat() if profile.last_study_date else None,
                "last_active": profile.last_active.isoformat() if profile.last_active else None
            },
            "progress": {
                "topics_studied": topics_studied,
                "active_plan_id": profile.active_plan_id,
                "active_plan_name": active_plan.plan_name if active_plan else None,
                "active_plan_completion": active_plan.completion_percentage if active_plan else 0.0,
                "learning_plans_count": len(profile.learning_plans),
                "learning_goals_count": len(profile.learning_goals),
                "topic_progress_count": len(profile.topic_progress),
                "assessment_history_count": len(profile.assessment_history)
            },
            "preferences": {
                "learning_approach": profile.learning_approach.value,
                "exam_preparation_mode": profile.exam_preparation_mode,
                "preferred_session_duration": profile.session_preferences.preferred_duration_minutes if profile.session_preferences else 60,
                "learning_style": profile.conversation_preferences.learning_style.value if profile.conversation_preferences else "adaptive"
            }
        }
    
    def reset_learning_progress(self, user_id: str, reset_type: str = "progress_only") -> bool:
        """Reset user's learning progress with different levels of reset."""
        profile = self.get_profile(user_id)
        if not profile:
            return False
        
        if reset_type == "progress_only":
            # Reset only learning progress, keep profile settings
            self._reset_progress_only(profile)
        elif reset_type == "learning_plans":
            # Reset learning plans and progress, keep profile
            self._reset_learning_plans(profile)
        elif reset_type == "full_reset":
            # Complete reset except username/email
            self._reset_full_profile(profile)
        elif reset_type == "refresh_current_plan":
            # Refresh current plan with latest topics
            self._refresh_current_plan(profile)
        
        self.save_profile(profile)
        return True
    
    def _reset_progress_only(self, profile: UserProfile):
        """Reset only learning progress, keep all settings."""
        # Reset all learning plans progress
        for plan in profile.learning_plans.values():
            for topic in plan.topics:
                topic.status = TopicStatus.NOT_STARTED
                topic.completion_date = None
                topic.user_marked_complete = False
            plan.current_topic_index = 0
            plan.completion_percentage = 0.0
            plan.topics_completed = 0
            plan.total_time_spent_minutes = 0
        
        # Reset topic progress
        profile.topic_progress = {}
        
        # Reset study statistics but keep profile settings
        profile.total_study_time_minutes = 0
        profile.sessions_completed = 0
        profile.average_session_duration_minutes = 0.0
        profile.streak_days = 0
        profile.last_study_date = None
        
        # Clear assessment history
        profile.assessment_history = []
    
    def _reset_learning_plans(self, profile: UserProfile):
        """Reset learning plans and progress, recreate with fresh templates."""
        # Clear all learning plans
        profile.learning_plans = {}
        profile.active_plan_id = None
        
        # Reset progress
        self._reset_progress_only(profile)
        
        # Clear learning goals
        profile.learning_goals = []
    
    def _reset_full_profile(self, profile: UserProfile):
        """Complete profile reset except basic identity."""
        # Keep only basic identity
        username = profile.username
        email = profile.email
        user_id = profile.user_id
        created_at = profile.created_at
        
        # Create a fresh profile without validation (don't call create_profile)
        from datetime import datetime

        # Reset all fields to defaults
        profile.experience_level = ExperienceLevel.BEGINNER
        profile.overall_proficiency = 0.0
        profile.target_certification = None
        profile.learning_approach = LearningApproach.STRUCTURED
        profile.structured_weight = 0.7
        profile.learning_plans = {}
        profile.active_plan_id = None
        profile.learning_goals = []
        profile.topic_progress = {}
        profile.proficiency_scores = {}
        profile.last_active = datetime.now()
        profile.last_study_date = None
        profile.total_study_time_minutes = 0
        profile.sessions_completed = 0
        profile.average_session_duration_minutes = 0.0
        profile.streak_days = 0
        profile.exam_preparation_mode = False
        profile.exam_readiness_score = 0.0
        profile.certification_deadline = None
        profile.assessment_history = []
        profile.strengths = []
        profile.areas_for_improvement = []
        profile.learning_velocity = 1.0
        profile.retention_score = 0.0
        profile.preferred_learning_times = []
        profile.knowledge_gaps = {}
        profile.last_assessment_date = None
        profile.current_session_id = None
        profile.current_topic_focus = None
        profile.profile_version = "2.0"
        profile.custom_tags = []
        profile.onboarding_completed = False  # Force re-onboarding
        profile.last_onboarding_step = ""
    
    def _refresh_current_plan(self, profile: UserProfile):
        """Refresh current plan with latest template topics."""
        if not profile.active_plan_id or profile.active_plan_id not in profile.learning_plans:
            return
        
        existing_plan = profile.learning_plans[profile.active_plan_id]
        plan_type = existing_plan.plan_type
        
        if plan_type in self.plan_templates:
            new_template = self.plan_templates[plan_type]
            
            # Update with new topics while preserving plan identity
            existing_plan.topics = new_template.topics
            existing_plan.estimated_total_duration_minutes = new_template.estimated_total_duration_minutes
            existing_plan.allow_topic_skipping = new_template.allow_topic_skipping
            existing_plan.enforce_prerequisites = new_template.enforce_prerequisites
            
            # Reset progress for the refreshed plan
            existing_plan.current_topic_index = 0
            existing_plan.completion_percentage = 0.0
            existing_plan.topics_completed = 0
            existing_plan.total_time_spent_minutes = 0