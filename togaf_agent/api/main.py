"""
FastAPI main application for TOGAF Agent REST API.
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

from .routers import users, onboarding, learning, sessions, chat
from ..utils.config import load_settings
from ..utils.openai_client import OpenAIClient
from ..user_management.user_profile import UserProfileManager
from ..user_management.onboarding import TOGAFOnboardingSystem
from ..user_management.progress_tracker import ProgressTracker
from ..conversation.session_manager import SessionManager
from ..conversation.adaptive_agent import AdaptiveAgent
from ..knowledge_base.semantic_search import TOGAFSemanticSearch


# Global application state
app_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - startup and shutdown."""
    
    # Startup
    logging.info("Starting TOGAF Agent API...")
    
    try:
        # Load configuration
        settings = load_settings()
        app_state["settings"] = settings
        
        # Initialize core components
        openai_client = OpenAIClient(settings)
        app_state["openai_client"] = openai_client
        
        # Initialize managers
        profile_manager = UserProfileManager()
        app_state["profile_manager"] = profile_manager
        
        onboarding_system = TOGAFOnboardingSystem(profile_manager)
        app_state["onboarding_system"] = onboarding_system
        
        progress_tracker = ProgressTracker(profile_manager)
        app_state["progress_tracker"] = progress_tracker
        
        session_manager = SessionManager(profile_manager)
        app_state["session_manager"] = session_manager
        
        # Initialize knowledge base components
        semantic_search = TOGAFSemanticSearch(settings)
        app_state["semantic_search"] = semantic_search
        
        # Initialize adaptive agent
        adaptive_agent = AdaptiveAgent(
            openai_client, semantic_search, progress_tracker, session_manager
        )
        app_state["adaptive_agent"] = adaptive_agent
        
        # Validate OpenAI connection
        api_valid = await openai_client.validate_api_key_async()
        if not api_valid:
            logging.warning("OpenAI API key validation failed - some features may not work")
        
        logging.info("TOGAF Agent API started successfully!")
        
        yield
        
    except Exception as e:
        logging.error(f"Failed to start TOGAF Agent API: {e}")
        raise
    
    # Shutdown
    logging.info("Shutting down TOGAF Agent API...")
    
    # Cleanup expired sessions
    if "session_manager" in app_state:
        try:
            expired_count = app_state["session_manager"].cleanup_expired_sessions()
            logging.info(f"Cleaned up {expired_count} expired sessions")
        except Exception as e:
            logging.error(f"Error during session cleanup: {e}")


# Create FastAPI application
app = FastAPI(
    title="TOGAF Agent API",
    description="REST API for the TOGAF learning and certification agent",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501", 
        "http://127.0.0.1:8501",
        "http://localhost:8502", 
        "http://127.0.0.1:8502"
    ],  # Streamlit default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


# Dependency injection helpers
def get_profile_manager() -> UserProfileManager:
    """Get the profile manager instance."""
    return app_state.get("profile_manager")

def get_onboarding_system() -> TOGAFOnboardingSystem:
    """Get the onboarding system instance."""
    return app_state.get("onboarding_system")

def get_progress_tracker() -> ProgressTracker:
    """Get the progress tracker instance."""
    return app_state.get("progress_tracker")

def get_session_manager() -> SessionManager:
    """Get the session manager instance."""
    return app_state.get("session_manager")

def get_adaptive_agent() -> AdaptiveAgent:
    """Get the adaptive agent instance."""
    return app_state.get("adaptive_agent")

def get_settings():
    """Get application settings."""
    return app_state.get("settings")


# Include routers
app.include_router(
    users.router, 
    prefix="/api/v1/users", 
    tags=["users"]
)

app.include_router(
    onboarding.router, 
    prefix="/api/v1/onboarding", 
    tags=["onboarding"]
)

app.include_router(
    learning.router, 
    prefix="/api/v1/learning", 
    tags=["learning"]
)

app.include_router(
    sessions.router, 
    prefix="/api/v1/sessions", 
    tags=["sessions"]
)

app.include_router(
    chat.router, 
    prefix="/api/v1/chat", 
    tags=["chat"]
)


# Root endpoints
@app.get("/")
async def root():
    """API root endpoint with basic information."""
    return {
        "message": "TOGAF Agent API",
        "version": "2.0.0",
        "status": "active",
        "endpoints": {
            "docs": "/docs",
            "users": "/api/v1/users",
            "onboarding": "/api/v1/onboarding", 
            "learning": "/api/v1/learning",
            "sessions": "/api/v1/sessions",
            "chat": "/api/v1/chat"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    
    health_status = {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "components": {}
    }
    
    # Check OpenAI connection
    openai_client = app_state.get("openai_client")
    if openai_client:
        try:
            api_valid = await openai_client.validate_api_key_async()
            health_status["components"]["openai"] = "healthy" if api_valid else "unhealthy"
        except Exception:
            health_status["components"]["openai"] = "unhealthy"
    else:
        health_status["components"]["openai"] = "not_initialized"
    
    # Check core components
    components = [
        "profile_manager", "onboarding_system", "progress_tracker",
        "session_manager", "adaptive_agent", "semantic_search"
    ]
    
    for component in components:
        if app_state.get(component):
            health_status["components"][component] = "healthy"
        else:
            health_status["components"][component] = "not_initialized"
    
    # Determine overall status
    unhealthy_components = [
        k for k, v in health_status["components"].items() 
        if v in ["unhealthy", "not_initialized"]
    ]
    
    if unhealthy_components:
        health_status["status"] = "degraded"
        health_status["issues"] = unhealthy_components
    
    return health_status

@app.get("/api/v1/system/info")
async def system_info():
    """Get system information and statistics."""
    
    info = {
        "api_version": "2.0.0",
        "system": {
            "components_loaded": len([k for k, v in app_state.items() if v is not None]),
            "total_components": 7
        }
    }
    
    # Add user statistics if profile manager is available
    profile_manager = app_state.get("profile_manager")
    if profile_manager:
        try:
            all_profiles = profile_manager.list_all_profiles()
            info["users"] = {
                "total_users": len(all_profiles),
                "active_users_30d": len([
                    p for p in all_profiles 
                    if (p.last_active and 
                        (p.last_active.replace(tzinfo=None) - 
                         datetime.now().replace(tzinfo=None)).days < 30)
                ]),
                "onboarding_completed": len([p for p in all_profiles if p.onboarding_completed])
            }
        except Exception as e:
            info["users"] = {"error": str(e)}
    
    # Add session statistics
    session_manager = app_state.get("session_manager")
    if session_manager:
        try:
            # This would need to be implemented in session_manager
            info["sessions"] = {
                "active_sessions": len(session_manager._active_sessions),
                "cached_sessions": len(session_manager._session_timeouts)
            }
        except Exception as e:
            info["sessions"] = {"error": str(e)}
    
    return info

@app.post("/api/v1/system/cleanup")
async def system_cleanup(background_tasks: BackgroundTasks):
    """Trigger system cleanup tasks."""
    
    def cleanup_task():
        """Background cleanup task."""
        results = {"cleaned_sessions": 0, "errors": []}
        
        # Cleanup expired sessions
        session_manager = app_state.get("session_manager")
        if session_manager:
            try:
                expired_count = session_manager.cleanup_expired_sessions()
                results["cleaned_sessions"] = expired_count
            except Exception as e:
                results["errors"].append(f"Session cleanup error: {str(e)}")
        
        logging.info(f"Cleanup completed: {results}")
        return results
    
    background_tasks.add_task(cleanup_task)
    
    return {
        "message": "Cleanup task scheduled",
        "status": "scheduled"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logging.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error", 
            "message": "An unexpected error occurred",
            "request_id": str(hash(str(request.url)))[:8]
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "togaf_agent.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )