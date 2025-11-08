"""
Agent API Routes
Control and monitor the Claude agent
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

router = APIRouter()

# Global agent instance (will be initialized at startup)
_agent_instance = None
_pipeline_instance = None


class CommandRequest(BaseModel):
    """Request to process a text command"""
    command: str = Field(..., description="Natural language command", min_length=1, max_length=500)
    speak_response: bool = Field(False, description="Whether to speak the response via TTS")


class CommandResponse(BaseModel):
    """Response from command processing"""
    success: bool
    response: str
    command: str
    timestamp: str


class AgentStatusResponse(BaseModel):
    """Agent status information"""
    active: bool
    mode: str
    model: str
    tools_available: int
    conversation_length: int


class ConversationMessage(BaseModel):
    """Single conversation message"""
    role: str
    content: str
    timestamp: Optional[str] = None


def set_agent_instance(agent, pipeline=None):
    """
    Set the global agent instance

    Called from FastAPI startup to inject the agent
    """
    global _agent_instance, _pipeline_instance
    _agent_instance = agent
    _pipeline_instance = pipeline


# ==================== COMMAND PROCESSING ====================

@router.post("/command", response_model=CommandResponse)
async def process_command(request: CommandRequest):
    """
    Process a text command through the agent

    This endpoint allows sending commands without voice input:
    - Useful for testing
    - Web interface integration
    - Debugging

    Example:
        POST /api/v1/agent/command
        {
            "command": "move forward 5 feet",
            "speak_response": false
        }
    """
    if _agent_instance is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )

    try:
        # Process command through agent
        response_text = await _agent_instance.process_command(request.command)

        # Optionally speak response
        if request.speak_response and hasattr(_agent_instance, 'voice_service'):
            try:
                await _agent_instance.voice_service.speak(response_text)
            except Exception as e:
                # Don't fail the request if TTS fails
                pass

        from datetime import datetime

        return CommandResponse(
            success=True,
            response=response_text,
            command=request.command,
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Command processing failed: {str(e)}"
        )


# ==================== AGENT STATUS ====================

@router.get("/status", response_model=AgentStatusResponse)
async def get_agent_status():
    """
    Get current agent status

    Returns:
        Agent status including mode, model, and conversation state
    """
    if _agent_instance is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )

    try:
        status_data = _agent_instance.get_agent_status()

        return AgentStatusResponse(
            active=status_data.get("active", False),
            mode=status_data.get("mode", "unknown"),
            model=status_data.get("model", "unknown"),
            tools_available=status_data.get("tools_available", 0),
            conversation_length=status_data.get("conversation_length", 0),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent status: {str(e)}"
        )


# ==================== CONVERSATION MANAGEMENT ====================

@router.get("/conversation")
async def get_conversation() -> Dict[str, Any]:
    """
    Get conversation history

    Returns:
        List of conversation messages with metadata
    """
    if _agent_instance is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )

    try:
        summary = _agent_instance.get_conversation_summary()

        return {
            "total_messages": summary.get("total_messages", 0),
            "mode": summary.get("mode", "unknown"),
            "messages": _agent_instance.conversation_history,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation: {str(e)}"
        )


@router.delete("/conversation")
async def clear_conversation():
    """
    Clear conversation history

    This resets the agent's conversation context
    """
    if _agent_instance is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )

    try:
        _agent_instance.clear_conversation()

        return {
            "success": True,
            "message": "Conversation history cleared"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear conversation: {str(e)}"
        )


# ==================== PIPELINE CONTROL ====================

@router.get("/pipeline/stats")
async def get_pipeline_stats() -> Dict[str, Any]:
    """
    Get voice pipeline statistics

    Returns:
        Pipeline stats including interaction count
    """
    if _pipeline_instance is None:
        return {
            "available": False,
            "message": "Voice pipeline not initialized"
        }

    try:
        stats = _pipeline_instance.get_stats()

        return {
            "available": True,
            **stats
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pipeline stats: {str(e)}"
        )


# ==================== HEALTH CHECK ====================

@router.get("/health")
async def health_check():
    """
    Health check endpoint

    Returns:
        Health status of the agent
    """
    if _agent_instance is None:
        return {
            "status": "unhealthy",
            "agent": "not_initialized",
            "timestamp": datetime.now().isoformat(),
        }

    try:
        agent_status = _agent_instance.get_agent_status()

        from datetime import datetime

        return {
            "status": "healthy",
            "agent": "initialized",
            "mode": agent_status.get("mode", "unknown"),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
