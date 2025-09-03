"""
User Management Module for TOGAF Agent.

This module handles user profiles, onboarding, and progress tracking.
"""

from .user_profile import (
    ExperienceLevel,
    LearningApproach,
    SessionIntensity,
    LearningStyle,
    LearningGoal,
    TopicProgress,
    ConversationPreferences,
    UserProfile,
    UserProfileManager
)

__all__ = [
    "ExperienceLevel",
    "LearningApproach", 
    "SessionIntensity",
    "LearningStyle",
    "LearningGoal",
    "TopicProgress",
    "ConversationPreferences",
    "UserProfile",
    "UserProfileManager"
]