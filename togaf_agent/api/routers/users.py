"""
User management API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from ...user_management.user_profile import UserProfileManager, UserProfile, LearningGoal
from ...user_management.progress_tracker import ProgressTracker


router = APIRouter()


# Request/Response models
class CreateUserRequest(BaseModel):
    username: str
    email: Optional[str] = None

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: Optional[str]
    created_at: datetime
    last_active: datetime
    experience_level: str
    overall_proficiency: float
    onboarding_completed: bool
    target_certification: Optional[str]
    active_plan_id: Optional[str]

class UpdateUserRequest(BaseModel):
    email: Optional[str] = None
    target_certification: Optional[str] = None
    exam_preparation_mode: Optional[bool] = None


# Import dependency from main app
def get_profile_manager_dep():
    """Get profile manager dependency - imported from main app."""
    from ..main import get_profile_manager
    return get_profile_manager()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    profile_manager: UserProfileManager = Depends(get_profile_manager_dep)
):
    """Create a new user profile."""
    try:
        profile = profile_manager.create_profile(
            username=request.username,
            email=request.email
        )
        
        return UserResponse(
            user_id=profile.user_id,
            username=profile.username,
            email=profile.email,
            created_at=profile.created_at,
            last_active=profile.last_active,
            experience_level=profile.experience_level.value,
            overall_proficiency=profile.overall_proficiency,
            onboarding_completed=profile.onboarding_completed,
            target_certification=profile.target_certification.value if profile.target_certification else None,
            active_plan_id=profile.active_plan_id
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    profile_manager: UserProfileManager = Depends(get_profile_manager_dep)
):
    """Get user profile by ID."""
    profile = profile_manager.get_profile(user_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        user_id=profile.user_id,
        username=profile.username,
        email=profile.email,
        created_at=profile.created_at,
        last_active=profile.last_active,
        experience_level=profile.experience_level.value,
        overall_proficiency=profile.overall_proficiency,
        onboarding_completed=profile.onboarding_completed,
        target_certification=profile.target_certification.value if profile.target_certification else None,
        active_plan_id=profile.active_plan_id
    )


@router.get("/username/{username}", response_model=UserResponse)
async def get_user_by_username(
    username: str,
    profile_manager: UserProfileManager = Depends(get_profile_manager_dep)
):
    """Get user profile by username."""
    profile = profile_manager.get_profile_by_username(username)
    
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        user_id=profile.user_id,
        username=profile.username,
        email=profile.email,
        created_at=profile.created_at,
        last_active=profile.last_active,
        experience_level=profile.experience_level.value,
        overall_proficiency=profile.overall_proficiency,
        onboarding_completed=profile.onboarding_completed,
        target_certification=profile.target_certification.value if profile.target_certification else None,
        active_plan_id=profile.active_plan_id
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    profile_manager: UserProfileManager = Depends(get_profile_manager_dep)
):
    """Update user profile."""
    profile = profile_manager.get_profile(user_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields if provided
    if request.email is not None:
        profile.email = request.email
    
    if request.target_certification is not None:
        from ...knowledge_base.metadata_schema import CertificationLevel
        profile.target_certification = CertificationLevel(request.target_certification)
    
    if request.exam_preparation_mode is not None:
        profile.exam_preparation_mode = request.exam_preparation_mode
    
    # Save updated profile
    profile_manager.save_profile(profile)
    
    return UserResponse(
        user_id=profile.user_id,
        username=profile.username,
        email=profile.email,
        created_at=profile.created_at,
        last_active=profile.last_active,
        experience_level=profile.experience_level.value,
        overall_proficiency=profile.overall_proficiency,
        onboarding_completed=profile.onboarding_completed,
        target_certification=profile.target_certification.value if profile.target_certification else None,
        active_plan_id=profile.active_plan_id
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    profile_manager: UserProfileManager = Depends(get_profile_manager_dep)
):
    """Delete a user profile."""
    success = profile_manager.delete_profile(user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}


@router.get("/")
async def list_users(
    limit: Optional[int] = 50,
    profile_manager: UserProfileManager = Depends(get_profile_manager_dep)
):
    """List all user profiles."""
    profiles = profile_manager.list_all_profiles()
    
    # Apply limit
    if limit:
        profiles = profiles[:limit]
    
    return [
        UserResponse(
            user_id=profile.user_id,
            username=profile.username,
            email=profile.email,
            created_at=profile.created_at,
            last_active=profile.last_active,
            experience_level=profile.experience_level.value,
            overall_proficiency=profile.overall_proficiency,
            onboarding_completed=profile.onboarding_completed,
            target_certification=profile.target_certification.value if profile.target_certification else None,
            active_plan_id=profile.active_plan_id
        )
        for profile in profiles
    ]


@router.get("/{user_id}/statistics")
async def get_user_statistics(
    user_id: str,
    profile_manager: UserProfileManager = Depends(get_profile_manager_dep)
):
    """Get comprehensive user statistics."""
    stats = profile_manager.get_user_statistics(user_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="User not found")
    
    return stats


@router.get("/{user_id}/learning-plans")
async def get_user_learning_plans(
    user_id: str,
    profile_manager: UserProfileManager = Depends(get_profile_manager_dep)
):
    """Get all learning plans for a user."""
    profile = profile_manager.get_profile(user_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    plans = {}
    for plan_id, plan in profile.learning_plans.items():
        plans[plan_id] = {
            "plan_id": plan.plan_id,
            "plan_name": plan.plan_name,
            "plan_type": plan.plan_type.value,
            "description": plan.description,
            "target_certification": plan.target_certification.value,
            "completion_percentage": plan.completion_percentage,
            "topics_completed": plan.topics_completed,
            "total_topics": len(plan.topics),
            "is_active": plan_id == profile.active_plan_id,
            "created_date": plan.created_date
        }
    
    return {"learning_plans": plans, "active_plan_id": profile.active_plan_id}


@router.get("/{user_id}/current-topic")
async def get_current_topic(
    user_id: str,
    profile_manager: UserProfileManager = Depends(get_profile_manager_dep)
):
    """Get current topic in user's active learning plan."""
    current_topic = profile_manager.get_current_topic(user_id)
    
    if not current_topic:
        return {"message": "No active learning plan or current topic"}
    
    return current_topic


@router.post("/{user_id}/topics/{topic_id}/complete")
async def mark_topic_complete(
    user_id: str,
    topic_id: str,
    profile_manager: UserProfileManager = Depends(get_profile_manager_dep)
):
    """Mark a topic as completed."""
    success = profile_manager.mark_topic_complete(user_id, topic_id, user_initiated=True)
    
    if not success:
        raise HTTPException(
            status_code=400, 
            detail="Failed to mark topic complete. User or active plan not found."
        )
    
    return {"message": f"Topic {topic_id} marked as complete"}


@router.post("/{user_id}/topics/{topic_id}/skip")
async def skip_topic(
    user_id: str,
    topic_id: str,
    profile_manager: UserProfileManager = Depends(get_profile_manager_dep)
):
    """Skip a topic in the learning plan."""
    success = profile_manager.skip_topic(user_id, topic_id)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Failed to skip topic. User, active plan not found, or skipping not allowed."
        )
    
    return {"message": f"Topic {topic_id} skipped"}


@router.get("/{user_id}/plan-overview")
async def get_plan_overview(
    user_id: str,
    plan_id: Optional[str] = None,
    profile_manager: UserProfileManager = Depends(get_profile_manager_dep)
):
    """Get detailed overview of user's learning plan."""
    overview = profile_manager.get_plan_overview(user_id, plan_id)
    
    if not overview:
        raise HTTPException(status_code=404, detail="User or learning plan not found")
    
    return overview


@router.post("/{user_id}/reset-learning")
async def reset_learning_progress(
    user_id: str,
    reset_type: str = "progress_only",  # options: progress_only, learning_plans, full_reset, refresh_current_plan
    profile_manager: UserProfileManager = Depends(get_profile_manager_dep)
):
    """Reset user's learning progress with different reset levels."""
    valid_reset_types = ["progress_only", "learning_plans", "full_reset", "refresh_current_plan"]
    
    if reset_type not in valid_reset_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid reset_type. Valid options: {valid_reset_types}"
        )
    
    success = profile_manager.reset_learning_progress(user_id, reset_type)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Failed to reset learning progress. User not found."
        )
    
    reset_messages = {
        "progress_only": "Learning progress reset successfully. Settings preserved.",
        "learning_plans": "Learning plans and progress reset successfully. Profile settings preserved.",
        "full_reset": "Complete profile reset successfully. Please complete onboarding again.",
        "refresh_current_plan": "Current learning plan refreshed with latest topics successfully."
    }
    
    return {"message": reset_messages.get(reset_type, "Learning progress reset successfully.")}