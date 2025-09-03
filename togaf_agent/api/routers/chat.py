"""
Chat and adaptive conversation API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, Optional
from pydantic import BaseModel

from ...conversation.adaptive_agent import AdaptiveAgent
from ...knowledge_base.metadata_schema import DifficultyLevel


router = APIRouter()


# Request/Response models
class ChatRequest(BaseModel):
    user_query: str
    user_id: str
    session_id: str
    context: Optional[Dict[str, Any]] = None

class ExplanationRequest(BaseModel):
    concept: str
    user_id: str
    session_id: str
    detail_level: str = "adaptive"

class ExamQuestionRequest(BaseModel):
    user_id: str
    topic_id: Optional[str] = None
    difficulty: Optional[str] = None


# Import dependency from main app
def get_adaptive_agent_dep():
    """Get adaptive agent dependency - imported from main app."""
    from ..main import get_adaptive_agent
    return get_adaptive_agent()


@router.post("/message")
async def send_chat_message(
    request: ChatRequest,
    adaptive_agent: AdaptiveAgent = Depends(get_adaptive_agent_dep)
):
    """Send a chat message and get adaptive response."""
    try:
        response = await adaptive_agent.generate_adaptive_response(
            request.user_query,
            request.user_id,
            request.session_id,
            request.context
        )
        
        return {
            "response_id": response.response_id,
            "primary_content": response.primary_content,
            "supplementary_content": response.supplementary_content,
            "visual_content": response.visual_content,
            "topics_addressed": response.topics_addressed,
            "concepts_explained": response.concepts_explained,
            "difficulty_level": response.difficulty_level.value,
            "response_style": response.response_style.value,
            "suggested_next_questions": response.suggested_next_questions,
            "recommended_practice": response.recommended_practice,
            "related_topics": response.related_topics,
            "timestamp": response.timestamp
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")


@router.post("/explain")
async def explain_concept(
    request: ExplanationRequest,
    adaptive_agent: AdaptiveAgent = Depends(get_adaptive_agent_dep)
):
    """Get adaptive explanation of a TOGAF concept."""
    try:
        response = await adaptive_agent.provide_explanation(
            request.concept,
            request.user_id,
            request.session_id,
            request.detail_level
        )
        
        return {
            "response_id": response.response_id,
            "primary_content": response.primary_content,
            "visual_content": response.visual_content,
            "topics_addressed": response.topics_addressed,
            "concepts_explained": response.concepts_explained,
            "difficulty_level": response.difficulty_level.value,
            "response_style": response.response_style.value,
            "suggested_next_questions": response.suggested_next_questions,
            "timestamp": response.timestamp
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {str(e)}")


@router.post("/exam-question")
async def generate_exam_question(
    request: ExamQuestionRequest,
    adaptive_agent: AdaptiveAgent = Depends(get_adaptive_agent_dep)
):
    """Generate adaptive exam questions based on user progress."""
    try:
        difficulty = None
        if request.difficulty:
            difficulty = DifficultyLevel(request.difficulty)
        
        question_data = await adaptive_agent.generate_exam_question(
            request.user_id,
            request.topic_id,
            difficulty
        )
        
        if "error" in question_data:
            raise HTTPException(status_code=500, detail=question_data["error"])
        
        return question_data
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid difficulty level: {request.difficulty}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate exam question: {str(e)}")


@router.get("/difficulty-levels")
async def get_difficulty_levels():
    """Get available difficulty levels."""
    levels = []
    
    for level in DifficultyLevel:
        level_info = {
            "level": level.value,
            "display_name": level.value.title(),
            "description": {
                "basic": "Fundamental concepts and definitions",
                "intermediate": "Applied knowledge and understanding", 
                "advanced": "Complex scenarios and expert-level topics"
            }.get(level.value, "")
        }
        levels.append(level_info)
    
    return {"difficulty_levels": levels}


@router.get("/explanation-levels")
async def get_explanation_levels():
    """Get available explanation detail levels."""
    levels = [
        {
            "level": "brief",
            "display_name": "Brief",
            "description": "Quick, concise explanations"
        },
        {
            "level": "moderate", 
            "display_name": "Moderate",
            "description": "Balanced detail level with examples"
        },
        {
            "level": "detailed",
            "display_name": "Detailed", 
            "description": "Comprehensive explanations with context"
        },
        {
            "level": "adaptive",
            "display_name": "Adaptive",
            "description": "Automatically adjusted based on user experience"
        }
    ]
    
    return {"explanation_levels": levels}