"""
Conversation session management API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from ...conversation.session_manager import SessionManager, ConversationMode, MessageType


router = APIRouter()


# Request/Response models
class CreateSessionRequest(BaseModel):
    user_id: str
    conversation_mode: str = "learning"
    initial_context: Optional[Dict[str, Any]] = None

class AddMessageRequest(BaseModel):
    message_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class UpdateContextRequest(BaseModel):
    context_updates: Dict[str, Any]


# Import dependency from main app
def get_session_manager_dep():
    """Get session manager dependency - imported from main app."""
    from ..main import get_session_manager
    return get_session_manager()


@router.post("/create")
async def create_session(
    request: CreateSessionRequest,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """Create a new conversation session."""
    try:
        conversation_mode = ConversationMode(request.conversation_mode)
        session_id = session_manager.create_session(
            request.user_id,
            conversation_mode,
            request.initial_context
        )
        
        return {"session_id": session_id, "status": "created"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid conversation mode: {request.conversation_mode}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """Get session details."""
    session = session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "created_at": session.created_at,
        "last_activity": session.last_activity,
        "expires_at": session.expires_at,
        "state": session.state.value,
        "conversation_mode": session.conversation_mode.value,
        "total_messages": session.total_messages,
        "topics_covered": session.topics_covered,
        "context": session.context.model_dump()
    }


@router.post("/{session_id}/messages")
async def add_message(
    session_id: str,
    request: AddMessageRequest,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """Add a message to the conversation session."""
    try:
        message_type = MessageType(request.message_type)
        success = session_manager.add_message(
            session_id,
            message_type,
            request.content,
            request.metadata
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found or inactive")
        
        return {"message": "Message added successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid message type: {request.message_type}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add message: {str(e)}")


@router.get("/{session_id}/messages")
async def get_conversation_history(
    session_id: str,
    limit: Optional[int] = None,
    message_types: Optional[List[str]] = None,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """Get conversation history with optional filtering."""
    try:
        # Convert string message types to enum
        type_filters = None
        if message_types:
            type_filters = [MessageType(mt) for mt in message_types]
        
        messages = session_manager.get_conversation_history(
            session_id, 
            limit, 
            type_filters
        )
        
        return {
            "messages": [
                {
                    "message_id": msg.message_id,
                    "timestamp": msg.timestamp,
                    "message_type": msg.message_type.value,
                    "content": msg.content,
                    "metadata": msg.metadata,
                    "topic_context": msg.topic_context,
                    "difficulty_level": msg.difficulty_level
                }
                for msg in messages
            ]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid message type in filter")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")


@router.put("/{session_id}/context")
async def update_context(
    session_id: str,
    request: UpdateContextRequest,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """Update session context with new information."""
    success = session_manager.update_context(session_id, request.context_updates)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Context updated successfully"}


@router.get("/{session_id}/context")
async def get_session_context(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """Get current session context for agent responses."""
    context = session_manager.get_session_context(session_id)
    
    if not context:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return context


@router.post("/{session_id}/pause")
async def pause_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """Pause an active session."""
    success = session_manager.pause_session(session_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Session not found or not active")
    
    return {"message": "Session paused successfully"}


@router.post("/{session_id}/resume")
async def resume_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """Resume a paused session."""
    success = session_manager.resume_session(session_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Session not found, not paused, or expired")
    
    return {"message": "Session resumed successfully"}


@router.post("/{session_id}/end")
async def end_session(
    session_id: str,
    satisfaction_score: Optional[float] = None,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """End a session and save final state."""
    success = session_manager.end_session(session_id, satisfaction_score)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session ended successfully"}


@router.get("/user/{user_id}/active")
async def get_user_active_session(
    user_id: str,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """Get the active session ID for a user."""
    session_id = session_manager.get_user_active_session(user_id)
    
    if not session_id:
        return {"active_session": None, "message": "No active session found"}
    
    return {"active_session": session_id}


@router.get("/user/{user_id}/statistics")
async def get_session_statistics(
    user_id: str,
    days: int = 30,
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """Get session statistics for a user."""
    stats = session_manager.get_session_statistics(user_id, days)
    
    return stats


@router.post("/cleanup")
async def cleanup_expired_sessions(
    session_manager: SessionManager = Depends(get_session_manager_dep)
):
    """Clean up expired sessions."""
    expired_count = session_manager.cleanup_expired_sessions()
    
    return {
        "message": f"Cleaned up {expired_count} expired sessions",
        "expired_count": expired_count
    }


@router.get("/modes")
async def get_conversation_modes():
    """Get available conversation modes."""
    modes = []
    
    for mode in ConversationMode:
        mode_info = {
            "mode": mode.value,
            "display_name": mode.value.replace("_", " ").title(),
            "description": {
                "learning": "General learning and concept exploration",
                "exam_prep": "Focused exam question practice and preparation", 
                "q_and_a": "Quick question and answer format",
                "assessment": "Knowledge assessment and evaluation",
                "review": "Review of previously learned concepts"
            }.get(mode.value, "")
        }
        modes.append(mode_info)
    
    return {"modes": modes}


@router.get("/message-types")
async def get_message_types():
    """Get available message types."""
    types = []
    
    for msg_type in MessageType:
        type_info = {
            "type": msg_type.value,
            "display_name": msg_type.value.replace("_", " ").title(),
            "description": {
                "user_question": "Question from the user",
                "agent_response": "Response from the TOGAF agent",
                "system_notification": "System-generated notification",
                "progress_update": "Learning progress update"
            }.get(msg_type.value, "")
        }
        types.append(type_info)
    
    return {"types": types}