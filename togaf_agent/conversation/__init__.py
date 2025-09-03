"""
Conversation Management Module for TOGAF Agent.

This module handles session management, conversation context, and adaptive responses.
"""

from .session_manager import (
    ConversationSession,
    SessionManager,
    ConversationContext,
    SessionState
)

__all__ = [
    "ConversationSession",
    "SessionManager", 
    "ConversationContext",
    "SessionState"
]