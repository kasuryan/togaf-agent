"""
User onboarding API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, Optional
from pydantic import BaseModel

from ...user_management.onboarding import TOGAFOnboardingSystem, OnboardingStep


router = APIRouter()


# Request/Response models
class StartOnboardingRequest(BaseModel):
    user_id: str

class ProcessStepRequest(BaseModel):
    user_id: str
    step: str
    response_data: Dict[str, Any]


# Import dependency from main app
def get_onboarding_system_dep():
    """Get onboarding system dependency - imported from main app."""
    from ..main import get_onboarding_system
    return get_onboarding_system()


@router.post("/start")
async def start_onboarding(
    request: StartOnboardingRequest,
    onboarding_system: TOGAFOnboardingSystem = Depends(get_onboarding_system_dep)
):
    """Start the onboarding process for a user."""
    try:
        result = onboarding_system.start_onboarding(request.user_id)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start onboarding: {str(e)}")


@router.post("/step")
async def process_step(
    request: ProcessStepRequest,
    onboarding_system: TOGAFOnboardingSystem = Depends(get_onboarding_system_dep)
):
    """Process a step in the onboarding flow."""
    try:
        step_enum = OnboardingStep(request.step)
        result = onboarding_system.process_step(
            request.user_id, 
            step_enum, 
            request.response_data
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid step: {request.step}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process step: {str(e)}")


@router.get("/progress/{user_id}")
async def get_onboarding_progress(
    user_id: str,
    onboarding_system: TOGAFOnboardingSystem = Depends(get_onboarding_system_dep)
):
    """Get current onboarding progress for a user."""
    progress = onboarding_system.get_onboarding_progress(user_id)
    
    if not progress:
        raise HTTPException(status_code=404, detail="Onboarding not started for this user")
    
    return progress


@router.get("/steps")
async def get_onboarding_steps():
    """Get list of all onboarding steps."""
    steps = []
    
    for step in OnboardingStep:
        step_info = {
            "step": step.value,
            "display_name": step.value.replace("_", " ").title(),
            "order": list(OnboardingStep).index(step)
        }
        steps.append(step_info)
    
    return {"steps": steps}