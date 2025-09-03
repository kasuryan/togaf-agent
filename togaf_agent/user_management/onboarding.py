"""
Smart user onboarding system for TOGAF Agent.
Assesses user proficiency and preferences to create personalized learning experience.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field

from .user_profile import (
    UserProfile, UserProfileManager, ExperienceLevel, LearningApproach, 
    SessionIntensity, LearningStyle, PlanType, LearningGoal
)
from ..knowledge_base.metadata_schema import CertificationLevel


class OnboardingStep(str, Enum):
    WELCOME = "welcome"
    EXPERIENCE_ASSESSMENT = "experience_assessment"
    LEARNING_PREFERENCES = "learning_preferences"
    GOAL_SETTING = "goal_setting"
    PLAN_SELECTION = "plan_selection"
    SESSION_PREFERENCES = "session_preferences"
    COMPLETION = "completion"


class AssessmentQuestion(BaseModel):
    question_id: str
    question_text: str
    question_type: str  # "multiple_choice", "rating", "yes_no", "open_ended"
    options: List[str] = Field(default_factory=list)
    correct_answer: Optional[str] = None
    difficulty_level: str = "basic"  # "basic", "intermediate", "advanced"
    topic_area: str = ""
    weight: float = 1.0  # Weight in overall assessment


class OnboardingState(BaseModel):
    user_id: str
    current_step: OnboardingStep = OnboardingStep.WELCOME
    step_data: Dict[str, Any] = Field(default_factory=dict)
    assessment_responses: Dict[str, Any] = Field(default_factory=dict)
    assessment_score: float = 0.0
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    is_complete: bool = False
    

class TOGAFOnboardingSystem:
    """Smart onboarding system for TOGAF learners."""
    
    def __init__(self, profile_manager: UserProfileManager):
        self.profile_manager = profile_manager
        self.assessment_questions = self._create_assessment_questions()
        self.onboarding_states: Dict[str, OnboardingState] = {}
    
    def start_onboarding(self, user_id: str) -> Dict[str, Any]:
        """Start the onboarding process for a new user."""
        profile = self.profile_manager.get_profile(user_id)
        if not profile:
            return {"error": "User not found"}
        
        if profile.onboarding_completed:
            return {"error": "User has already completed onboarding"}
        
        # Initialize onboarding state
        onboarding_state = OnboardingState(user_id=user_id)
        self.onboarding_states[user_id] = onboarding_state
        
        # Update profile
        profile.last_onboarding_step = OnboardingStep.WELCOME.value
        self.profile_manager.save_profile(profile)
        
        return self._get_welcome_step()
    
    def process_step(self, user_id: str, step: OnboardingStep, 
                    response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a step in the onboarding flow."""
        onboarding_state = self.onboarding_states.get(user_id)
        if not onboarding_state:
            return {"error": "Onboarding not started"}
        
        # Process current step
        if step == OnboardingStep.WELCOME:
            return self._process_welcome_step(onboarding_state, response_data)
        elif step == OnboardingStep.EXPERIENCE_ASSESSMENT:
            return self._process_experience_assessment(onboarding_state, response_data)
        elif step == OnboardingStep.LEARNING_PREFERENCES:
            return self._process_learning_preferences(onboarding_state, response_data)
        elif step == OnboardingStep.GOAL_SETTING:
            return self._process_goal_setting(onboarding_state, response_data)
        elif step == OnboardingStep.PLAN_SELECTION:
            return self._process_plan_selection(onboarding_state, response_data)
        elif step == OnboardingStep.SESSION_PREFERENCES:
            return self._process_session_preferences(onboarding_state, response_data)
        else:
            return {"error": f"Unknown step: {step}"}
    
    def _get_welcome_step(self) -> Dict[str, Any]:
        """Get welcome step content."""
        return {
            "step": OnboardingStep.WELCOME.value,
            "title": "Welcome to your TOGAF Learning Journey! 🎯",
            "content": [
                "I'm your AI-powered TOGAF tutor, designed to help you master enterprise architecture.",
                "Let me ask a few questions to create a personalized learning experience for you.",
                "",
                "This will take about 5-10 minutes and will help me:",
                "• Assess your current TOGAF knowledge level",
                "• Understand your learning preferences",
                "• Create a customized study plan",
                "• Set up your ideal learning environment"
            ],
            "question": "Are you ready to get started?",
            "options": ["Yes, let's begin!", "I need more information first"],
            "next_step": OnboardingStep.EXPERIENCE_ASSESSMENT.value
        }
    
    def _process_welcome_step(self, state: OnboardingState, 
                            response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process welcome step response."""
        response = response_data.get("response", "")
        
        state.step_data["welcome_response"] = response
        state.current_step = OnboardingStep.EXPERIENCE_ASSESSMENT
        
        if "more information" in response.lower():
            # Provide additional information
            return {
                "step": OnboardingStep.WELCOME.value,
                "title": "About Your TOGAF Learning Experience",
                "content": [
                    "🎓 **Personalized Learning**: Adapted to your experience level and goals",
                    "📚 **Comprehensive Content**: Foundation and Practitioner level materials",
                    "🎯 **Exam Preparation**: Practice questions and gap analysis",
                    "⏱️ **Flexible Sessions**: Study at your own pace with customizable session lengths",
                    "📊 **Progress Tracking**: Monitor your learning journey and achievements",
                    "🔄 **Adaptive Content**: Content difficulty adjusts based on your performance"
                ],
                "question": "Ready to create your personalized learning plan?",
                "options": ["Yes, let's get started!"],
                "next_step": OnboardingStep.EXPERIENCE_ASSESSMENT.value
            }
        
        return self._get_experience_assessment_step()
    
    def _get_experience_assessment_step(self) -> Dict[str, Any]:
        """Get experience assessment step with adaptive questions."""
        return {
            "step": OnboardingStep.EXPERIENCE_ASSESSMENT.value,
            "title": "Let's Assess Your TOGAF Knowledge 🧠",
            "content": [
                "I'll ask you a few questions to understand your current level.",
                "Don't worry if you don't know all the answers - this helps me tailor your learning!"
            ],
            "assessment": {
                "questions": [q.model_dump() for q in self.assessment_questions[:5]],  # Start with first 5
                "total_questions": len(self.assessment_questions),
                "instruction": "Select the best answer for each question. If you're unsure, choose 'I don't know' - there's no penalty!"
            },
            "next_step": OnboardingStep.LEARNING_PREFERENCES.value
        }
    
    def _process_experience_assessment(self, state: OnboardingState, 
                                     response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process experience assessment responses."""
        responses = response_data.get("responses", {})
        state.assessment_responses = responses
        
        # Calculate assessment score
        total_score = 0
        total_weight = 0
        
        for question in self.assessment_questions:
            response = responses.get(question.question_id, "")
            if response == question.correct_answer:
                total_score += question.weight
            total_weight += question.weight
        
        assessment_score = (total_score / total_weight) if total_weight > 0 else 0
        state.assessment_score = assessment_score
        
        # Determine experience level
        if assessment_score >= 0.8:
            experience_level = ExperienceLevel.EXPERT
        elif assessment_score >= 0.6:
            experience_level = ExperienceLevel.ADVANCED
        elif assessment_score >= 0.3:
            experience_level = ExperienceLevel.INTERMEDIATE
        else:
            experience_level = ExperienceLevel.BEGINNER
        
        state.step_data["determined_experience_level"] = experience_level.value
        state.current_step = OnboardingStep.LEARNING_PREFERENCES
        
        # Update user profile
        profile = self.profile_manager.get_profile(state.user_id)
        if profile:
            profile.experience_level = experience_level
            profile.overall_proficiency = assessment_score
            profile.last_onboarding_step = OnboardingStep.LEARNING_PREFERENCES.value
            self.profile_manager.save_profile(profile)
        
        return self._get_learning_preferences_step(experience_level, assessment_score)
    
    def _get_learning_preferences_step(self, experience_level: ExperienceLevel, 
                                     score: float) -> Dict[str, Any]:
        """Get learning preferences step."""
        score_feedback = ""
        if score >= 0.8:
            score_feedback = "Excellent! You have strong TOGAF knowledge."
        elif score >= 0.6:
            score_feedback = "Great! You have solid foundational knowledge."
        elif score >= 0.3:
            score_feedback = "Good start! You have some TOGAF familiarity."
        else:
            score_feedback = "Perfect! We'll start with the fundamentals."
        
        return {
            "step": OnboardingStep.LEARNING_PREFERENCES.value,
            "title": "Understanding Your Learning Style 🎨",
            "feedback": f"Assessment complete! {score_feedback}",
            "experience_level": f"Detected level: {experience_level.value.title()}",
            "content": [
                "Now let's understand how you prefer to learn.",
                "This helps me present information in the most effective way for you."
            ],
            "questions": [
                {
                    "id": "learning_approach",
                    "question": "How do you prefer to structure your learning?",
                    "type": "single_choice",
                    "options": [
                        {
                            "value": LearningApproach.STRUCTURED.value,
                            "label": "Structured path - Follow a step-by-step curriculum",
                            "description": "Best for systematic learning and certification prep"
                        },
                        {
                            "value": LearningApproach.ADHOC.value,
                            "label": "On-demand - Learn specific topics as needed",
                            "description": "Great for immediate problem-solving and flexibility"
                        },
                        {
                            "value": LearningApproach.HYBRID.value,
                            "label": "Hybrid - Mix of structured and on-demand learning",
                            "description": "Balanced approach with flexibility"
                        }
                    ]
                },
                {
                    "id": "learning_style",
                    "question": "How do you learn best?",
                    "type": "single_choice",
                    "options": [
                        {
                            "value": LearningStyle.VISUAL.value,
                            "label": "Visual - Diagrams, charts, and visual representations",
                            "description": "I prefer visual aids and diagrams"
                        },
                        {
                            "value": LearningStyle.READING_WRITING.value,
                            "label": "Reading/Writing - Text-based explanations and notes",
                            "description": "I learn well from detailed text and taking notes"
                        }
                    ]
                },
                {
                    "id": "explanation_depth",
                    "question": "How detailed should my explanations be?",
                    "type": "single_choice",
                    "options": [
                        {"value": "brief", "label": "Brief - Quick, concise explanations"},
                        {"value": "moderate", "label": "Moderate - Balanced detail level"},
                        {"value": "detailed", "label": "Detailed - Comprehensive explanations"}
                    ]
                }
            ],
            "next_step": OnboardingStep.GOAL_SETTING.value
        }
    
    def _process_learning_preferences(self, state: OnboardingState, 
                                    response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process learning preferences responses."""
        preferences = response_data.get("preferences", {})
        state.step_data["learning_preferences"] = preferences
        state.current_step = OnboardingStep.GOAL_SETTING
        
        # Update user profile
        profile = self.profile_manager.get_profile(state.user_id)
        if profile:
            # Update learning preferences
            if "learning_approach" in preferences:
                profile.learning_approach = LearningApproach(preferences["learning_approach"])
            
            if "learning_style" in preferences:
                profile.conversation_preferences.learning_style = LearningStyle(preferences["learning_style"])
            
            if "explanation_depth" in preferences:
                profile.conversation_preferences.explanation_depth = preferences["explanation_depth"]
            
            profile.last_onboarding_step = OnboardingStep.GOAL_SETTING.value
            self.profile_manager.save_profile(profile)
        
        return self._get_goal_setting_step()
    
    def _get_goal_setting_step(self) -> Dict[str, Any]:
        """Get goal setting step."""
        return {
            "step": OnboardingStep.GOAL_SETTING.value,
            "title": "Setting Your Learning Goals 🎯",
            "content": [
                "What would you like to achieve with TOGAF?",
                "Your goals will help me prioritize the most relevant content for you."
            ],
            "questions": [
                {
                    "id": "primary_goal",
                    "question": "What's your primary learning goal?",
                    "type": "single_choice",
                    "options": [
                        {
                            "value": "foundation_cert",
                            "label": "TOGAF Foundation Certification",
                            "description": "Pass the Foundation level exam"
                        },
                        {
                            "value": "practitioner_cert",
                            "label": "TOGAF Practitioner Certification",
                            "description": "Advance to Practitioner level"
                        },
                        {
                            "value": "practical_knowledge",
                            "label": "Practical Knowledge",
                            "description": "Learn to apply TOGAF in real projects"
                        },
                        {
                            "value": "general_understanding",
                            "label": "General Understanding",
                            "description": "Gain overall understanding of enterprise architecture"
                        }
                    ]
                },
                {
                    "id": "exam_preparation",
                    "question": "Are you preparing for a certification exam?",
                    "type": "yes_no",
                    "follow_up": {
                        "yes": {
                            "question": "When do you plan to take the exam?",
                            "type": "single_choice",
                            "options": [
                                {"value": "1_month", "label": "Within 1 month"},
                                {"value": "3_months", "label": "Within 3 months"},
                                {"value": "6_months", "label": "Within 6 months"},
                                {"value": "flexible", "label": "Flexible timeline"}
                            ]
                        }
                    }
                },
                {
                    "id": "focus_areas",
                    "question": "Any specific TOGAF areas you want to focus on?",
                    "type": "multiple_choice",
                    "options": [
                        {"value": "adm", "label": "Architecture Development Method (ADM)"},
                        {"value": "governance", "label": "Architecture Governance"},
                        {"value": "frameworks", "label": "Architecture Frameworks"},
                        {"value": "modeling", "label": "Architecture Modeling"},
                        {"value": "implementation", "label": "Implementation and Migration"},
                        {"value": "all", "label": "Comprehensive coverage of all areas"}
                    ]
                }
            ],
            "next_step": OnboardingStep.PLAN_SELECTION.value
        }
    
    def _process_goal_setting(self, state: OnboardingState, 
                            response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process goal setting responses."""
        goals = response_data.get("goals", {})
        state.step_data["goals"] = goals
        state.current_step = OnboardingStep.PLAN_SELECTION
        
        # Update user profile with goals
        profile = self.profile_manager.get_profile(state.user_id)
        if profile:
            # Set target certification
            primary_goal = goals.get("primary_goal", "")
            if "foundation" in primary_goal:
                profile.target_certification = CertificationLevel.FOUNDATION
            elif "practitioner" in primary_goal:
                profile.target_certification = CertificationLevel.PRACTITIONER
            
            # Set exam preparation mode
            exam_prep = goals.get("exam_preparation", False)
            profile.exam_preparation_mode = exam_prep
            
            # Create learning goal
            goal_description = self._create_goal_description(goals)
            learning_goal = LearningGoal(
                certification_level=profile.target_certification or CertificationLevel.FOUNDATION,
                description=goal_description,
                priority=1
            )
            profile.learning_goals.append(learning_goal)
            
            profile.last_onboarding_step = OnboardingStep.PLAN_SELECTION.value
            self.profile_manager.save_profile(profile)
        
        return self._get_plan_selection_step(state)
    
    def _get_plan_selection_step(self, state: OnboardingState) -> Dict[str, Any]:
        """Get plan selection step based on user assessment and goals."""
        experience_level = state.step_data.get("determined_experience_level", "beginner")
        goals = state.step_data.get("goals", {})
        preferences = state.step_data.get("learning_preferences", {})
        
        # Recommend plans based on user profile
        recommended_plans = []
        
        if experience_level == "beginner":
            recommended_plans.append({
                "type": PlanType.FOUNDATION_BEGINNER.value,
                "name": "TOGAF Foundation for Beginners",
                "description": "Comprehensive step-by-step introduction to TOGAF",
                "duration": "8-12 hours",
                "recommended": True
            })
        
        if experience_level in ["intermediate", "advanced", "expert"]:
            recommended_plans.append({
                "type": PlanType.FOUNDATION_REVIEW.value,
                "name": "TOGAF Foundation Review",
                "description": "Quick review of key Foundation concepts",
                "duration": "4-6 hours",
                "recommended": experience_level != "beginner"
            })
        
        if goals.get("primary_goal") == "practitioner_cert":
            recommended_plans.append({
                "type": PlanType.PRACTITIONER_PREP.value,
                "name": "TOGAF Practitioner Preparation",
                "description": "Advanced topics and practical applications",
                "duration": "10-15 hours",
                "recommended": experience_level in ["advanced", "expert"]
            })
        
        # Always offer custom option
        recommended_plans.append({
            "type": PlanType.CUSTOM_TOPICS.value,
            "name": "Custom Topic Selection",
            "description": "Choose specific topics you want to focus on",
            "duration": "Variable",
            "recommended": False
        })
        
        return {
            "step": OnboardingStep.PLAN_SELECTION.value,
            "title": "Choose Your Learning Plan 📚",
            "content": [
                "Based on your assessment and goals, here are the recommended learning plans:",
                "You can always change or customize your plan later."
            ],
            "recommended_plans": recommended_plans,
            "question": "Which learning plan would you like to start with?",
            "next_step": OnboardingStep.SESSION_PREFERENCES.value
        }
    
    def _process_plan_selection(self, state: OnboardingState, 
                              response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process plan selection response."""
        selected_plan = response_data.get("selected_plan", "")
        custom_topics = response_data.get("custom_topics", [])
        
        state.step_data["selected_plan"] = selected_plan
        state.step_data["custom_topics"] = custom_topics
        state.current_step = OnboardingStep.SESSION_PREFERENCES
        
        # Create learning plan for user
        profile = self.profile_manager.get_profile(state.user_id)
        if profile:
            try:
                plan_type = PlanType(selected_plan)
                plan_id = self.profile_manager.create_structured_plan(
                    state.user_id, 
                    plan_type, 
                    custom_topics if plan_type == PlanType.CUSTOM_TOPICS else None
                )
                state.step_data["created_plan_id"] = plan_id
            except ValueError:
                # Handle invalid plan type
                pass
            
            profile.last_onboarding_step = OnboardingStep.SESSION_PREFERENCES.value
            self.profile_manager.save_profile(profile)
        
        return self._get_session_preferences_step()
    
    def _get_session_preferences_step(self) -> Dict[str, Any]:
        """Get session preferences step."""
        return {
            "step": OnboardingStep.SESSION_PREFERENCES.value,
            "title": "Customize Your Learning Sessions ⚙️",
            "content": [
                "Finally, let's set up your ideal learning sessions.",
                "These settings help me provide the best learning experience."
            ],
            "questions": [
                {
                    "id": "session_duration",
                    "question": "How long would you like your typical learning session to be?",
                    "type": "single_choice",
                    "options": [
                        {"value": "15", "label": "15 minutes - Quick learning bursts"},
                        {"value": "30", "label": "30 minutes - Balanced sessions"},
                        {"value": "45", "label": "45 minutes - Deep focus sessions"},
                        {"value": "60", "label": "60+ minutes - Intensive study sessions"}
                    ]
                },
                {
                    "id": "session_intensity",
                    "question": "What intensity level works best for you?",
                    "type": "single_choice",
                    "options": [
                        {
                            "value": SessionIntensity.LIGHT.value,
                            "label": "Light - Relaxed pace, more examples",
                            "description": "Perfect for casual learning"
                        },
                        {
                            "value": SessionIntensity.MODERATE.value,
                            "label": "Moderate - Balanced pace and depth",
                            "description": "Good balance of pace and comprehension"
                        },
                        {
                            "value": SessionIntensity.INTENSIVE.value,
                            "label": "Intensive - Fast pace, comprehensive coverage",
                            "description": "Maximum information density"
                        }
                    ]
                },
                {
                    "id": "interaction_style",
                    "question": "How interactive should our sessions be?",
                    "type": "single_choice",
                    "options": [
                        {"value": "high", "label": "High - Frequent questions and exercises"},
                        {"value": "moderate", "label": "Moderate - Some interaction and check-ins"},
                        {"value": "low", "label": "Low - Focus on content delivery"}
                    ]
                }
            ],
            "next_step": OnboardingStep.COMPLETION.value
        }
    
    def _process_session_preferences(self, state: OnboardingState, 
                                   response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process session preferences and complete onboarding."""
        session_prefs = response_data.get("session_preferences", {})
        state.step_data["session_preferences"] = session_prefs
        
        # Update user profile
        profile = self.profile_manager.get_profile(state.user_id)
        if profile:
            # Update session preferences
            if "session_duration" in session_prefs:
                profile.session_preferences.preferred_duration_minutes = int(session_prefs["session_duration"])
            
            if "session_intensity" in session_prefs:
                profile.session_preferences.session_intensity = SessionIntensity(session_prefs["session_intensity"])
            
            if "interaction_style" in session_prefs:
                interactive_level = session_prefs["interaction_style"]
                profile.conversation_preferences.interactive_mode = interactive_level in ["high", "moderate"]
            
            # Mark onboarding as completed
            profile.onboarding_completed = True
            profile.last_onboarding_step = OnboardingStep.COMPLETION.value
            self.profile_manager.save_profile(profile)
        
        # Complete onboarding state
        state.current_step = OnboardingStep.COMPLETION
        state.completed_at = datetime.now()
        state.is_complete = True
        
        return self._get_completion_step(state)
    
    def _get_completion_step(self, state: OnboardingState) -> Dict[str, Any]:
        """Get onboarding completion step."""
        experience_level = state.step_data.get("determined_experience_level", "beginner")
        selected_plan = state.step_data.get("selected_plan", "")
        
        # Create personalized welcome message
        profile = self.profile_manager.get_profile(state.user_id)
        plan_info = ""
        if profile and profile.active_plan_id:
            active_plan = profile.learning_plans.get(profile.active_plan_id)
            if active_plan:
                plan_info = f"Your **{active_plan.plan_name}** is ready with {len(active_plan.topics)} topics!"
        
        return {
            "step": OnboardingStep.COMPLETION.value,
            "title": "Welcome to Your TOGAF Journey! 🎉",
            "content": [
                f"Perfect! Your personalized learning environment is set up.",
                f"**Experience Level**: {experience_level.title()}",
                f"**Assessment Score**: {state.assessment_score:.1%}",
                "",
                plan_info,
                "",
                "**What's Next?**",
                "• Start your first learning session",
                "• Explore your personalized learning plan", 
                "• Ask me questions anytime during your journey",
                "• Track your progress and celebrate achievements!",
                "",
                "I'm here to guide you every step of the way. Let's begin! 🚀"
            ],
            "onboarding_complete": True,
            "next_actions": [
                {"action": "start_session", "label": "Start First Learning Session"},
                {"action": "view_plan", "label": "View My Learning Plan"},
                {"action": "ask_question", "label": "Ask a Question"}
            ]
        }
    
    def _create_assessment_questions(self) -> List[AssessmentQuestion]:
        """Create a set of assessment questions to evaluate TOGAF knowledge."""
        import random
        
        questions = [
            AssessmentQuestion(
                question_id="togaf_definition",
                question_text="What does TOGAF stand for?",
                question_type="multiple_choice",
                options=[
                    "The Open Group Architecture Framework",
                    "Total Organization Governance and Framework",
                    "Technology Operations and Governance Framework",
                    "I don't know"
                ],
                correct_answer="The Open Group Architecture Framework",
                difficulty_level="basic",
                topic_area="introduction"
            ),
            AssessmentQuestion(
                question_id="adm_purpose",
                question_text="What is the primary purpose of the TOGAF ADM?",
                question_type="multiple_choice",
                options=[
                    "To provide a tested and repeatable process for developing architectures",
                    "To create software applications",
                    "To manage IT projects",
                    "I don't know"
                ],
                correct_answer="To provide a tested and repeatable process for developing architectures",
                difficulty_level="basic",
                topic_area="adm"
            ),
            AssessmentQuestion(
                question_id="adm_phases",
                question_text="How many main phases does the TOGAF ADM have?",
                question_type="multiple_choice",
                options=[
                    "6 phases",
                    "8 phases plus Preliminary Phase",
                    "10 phases",
                    "I don't know"
                ],
                correct_answer="8 phases plus Preliminary Phase",
                difficulty_level="intermediate",
                topic_area="adm"
            ),
            AssessmentQuestion(
                question_id="architecture_domains",
                question_text="What are the four architecture domains in TOGAF?",
                question_type="multiple_choice",
                options=[
                    "Business, Data, Application, Technology",
                    "Strategy, Process, Information, Infrastructure", 
                    "Planning, Design, Implementation, Governance",
                    "I don't know"
                ],
                correct_answer="Business, Data, Application, Technology",
                difficulty_level="intermediate",
                topic_area="architecture_domains"
            ),
            AssessmentQuestion(
                question_id="preliminary_phase",
                question_text="What is the main purpose of the Preliminary Phase?",
                question_type="multiple_choice",
                options=[
                    "To prepare and initiate the architecture development cycle",
                    "To create the business architecture",
                    "To implement the target architecture",
                    "I don't know"
                ],
                correct_answer="To prepare and initiate the architecture development cycle",
                difficulty_level="intermediate",
                topic_area="preliminary_phase"
            )
        ]
        
        # Randomize the order of options for each question
        for question in questions:
            if question.question_type == "multiple_choice" and len(question.options) > 1:
                # Keep "I don't know" at the end if it exists
                dont_know_option = None
                other_options = []
                
                for option in question.options:
                    if "I don't know" in option or "don't know" in option.lower():
                        dont_know_option = option
                    else:
                        other_options.append(option)
                
                # Shuffle only the non-"I don't know" options
                random.shuffle(other_options)
                
                # Reconstruct the options list
                question.options = other_options[:]
                if dont_know_option:
                    question.options.append(dont_know_option)
        
        return questions
    
    def _create_goal_description(self, goals: Dict[str, Any]) -> str:
        """Create a readable goal description from user responses."""
        primary_goal = goals.get("primary_goal", "")
        exam_prep = goals.get("exam_preparation", False)
        
        descriptions = {
            "foundation_cert": "Achieve TOGAF Foundation certification",
            "practitioner_cert": "Achieve TOGAF Practitioner certification",
            "practical_knowledge": "Learn to apply TOGAF in real-world projects",
            "general_understanding": "Gain comprehensive understanding of enterprise architecture"
        }
        
        base_description = descriptions.get(primary_goal, "Master TOGAF enterprise architecture")
        
        if exam_prep:
            base_description += " with focused exam preparation"
        
        return base_description
    
    def get_onboarding_progress(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current onboarding progress for a user."""
        state = self.onboarding_states.get(user_id)
        if not state:
            return None
        
        steps = list(OnboardingStep)
        current_index = steps.index(state.current_step)
        progress_percentage = (current_index / len(steps)) * 100
        
        return {
            "current_step": state.current_step.value,
            "progress_percentage": progress_percentage,
            "is_complete": state.is_complete,
            "steps_completed": current_index,
            "total_steps": len(steps),
            "started_at": state.started_at.isoformat(),
            "completed_at": state.completed_at.isoformat() if state.completed_at else None
        }