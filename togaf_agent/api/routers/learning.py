"""
Learning progress and analytics API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from ...user_management.progress_tracker import ProgressTracker, LearningPathType


router = APIRouter()


# Request/Response models
class StartSessionRequest(BaseModel):
    user_id: str
    session_type: str = "general"

class EndSessionRequest(BaseModel):
    satisfaction_score: Optional[float] = None

class TopicInteractionRequest(BaseModel):
    session_id: str
    topic_id: str
    interaction_type: str
    success: bool = True

class UpdateProficiencyRequest(BaseModel):
    user_id: str
    topic_id: str
    performance_data: Dict[str, Any]

class CreateLearningPathRequest(BaseModel):
    user_id: str
    path_type: str = "adaptive"


# Import dependency from main app
def get_progress_tracker_dep():
    """Get progress tracker dependency - imported from main app."""
    from ..main import get_progress_tracker
    return get_progress_tracker()


@router.post("/sessions/start")
async def start_learning_session(
    request: StartSessionRequest,
    progress_tracker: ProgressTracker = Depends(get_progress_tracker_dep)
):
    """Start a new learning session for tracking."""
    try:
        session_id = progress_tracker.start_learning_session(
            request.user_id, 
            request.session_type
        )
        
        return {"session_id": session_id, "status": "started"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")


@router.post("/sessions/{session_id}/end")
async def end_learning_session(
    session_id: str,
    request: EndSessionRequest,
    progress_tracker: ProgressTracker = Depends(get_progress_tracker_dep)
):
    """End a learning session and save analytics."""
    success = progress_tracker.end_learning_session(session_id, request.satisfaction_score)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session ended successfully", "session_id": session_id}


@router.post("/sessions/interaction")
async def log_topic_interaction(
    request: TopicInteractionRequest,
    progress_tracker: ProgressTracker = Depends(get_progress_tracker_dep)
):
    """Log user interaction with a topic during a session."""
    success = progress_tracker.log_topic_interaction(
        request.session_id,
        request.topic_id,
        request.interaction_type,
        request.success
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Interaction logged successfully"}


@router.post("/proficiency/update")
async def update_topic_proficiency(
    request: UpdateProficiencyRequest,
    progress_tracker: ProgressTracker = Depends(get_progress_tracker_dep)
):
    """Update topic proficiency based on performance data."""
    success = progress_tracker.update_topic_proficiency(
        request.user_id,
        request.topic_id,
        request.performance_data
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update proficiency")
    
    return {"message": "Proficiency updated successfully"}


@router.get("/analytics/{user_id}")
async def get_progress_analytics(
    user_id: str,
    force_refresh: bool = False,
    progress_tracker: ProgressTracker = Depends(get_progress_tracker_dep)
):
    """Get comprehensive progress analytics for a user."""
    analytics = progress_tracker.get_progress_analytics(user_id, force_refresh)
    
    if not analytics:
        raise HTTPException(status_code=404, detail="User not found")
    
    return analytics.model_dump()


@router.post("/learning-path/create")
async def create_adaptive_learning_path(
    request: CreateLearningPathRequest,
    progress_tracker: ProgressTracker = Depends(get_progress_tracker_dep)
):
    """Create an adaptive learning path for a user."""
    try:
        path_type = LearningPathType(request.path_type)
        path_id = progress_tracker.create_adaptive_learning_path(request.user_id, path_type)
        
        if not path_id:
            raise HTTPException(status_code=400, detail="Failed to create learning path")
        
        return {"path_id": path_id, "message": "Learning path created successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid path type: {request.path_type}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create learning path: {str(e)}")


@router.get("/recommendations/{user_id}")
async def get_next_recommended_topics(
    user_id: str,
    count: int = 3,
    progress_tracker: ProgressTracker = Depends(get_progress_tracker_dep)
):
    """Get next recommended topics based on adaptive learning path."""
    recommendations = progress_tracker.get_next_recommended_topics(user_id, count)
    
    return {"recommendations": recommendations}


@router.get("/insights/{user_id}")
async def get_learning_insights(
    user_id: str,
    progress_tracker: ProgressTracker = Depends(get_progress_tracker_dep)
):
    """Get personalized learning insights and recommendations."""
    insights = progress_tracker.get_learning_insights(user_id)
    
    if not insights:
        raise HTTPException(status_code=404, detail="User not found")
    
    return insights


@router.get("/path-types")
async def get_learning_path_types():
    """Get available learning path types."""
    path_types = []
    
    for path_type in LearningPathType:
        type_info = {
            "type": path_type.value,
            "display_name": path_type.value.replace("_", " ").title(),
            "description": {
                "linear": "Follow a predetermined sequence of topics",
                "adaptive": "Dynamically adjust based on performance and gaps",
                "personalized": "Customized based on user goals and preferences",
                "exam_focused": "Optimized for certification exam preparation"
            }.get(path_type.value, "")
        }
        path_types.append(type_info)
    
    return {"path_types": path_types}