"""
Nura - Agent Exceptions
"""
from app.core.exceptions import AIError

class AgentException(AIError):
    """Base exception for all agent errors"""
    pass

class AgentValidationError(AgentException):
    """Raised when input or state validation failed"""
    pass

class AgentExecutionError(AgentException):
    """Raised when error occurs during agent execution"""
    pass

class AgentTimeoutError(AgentException):
    """Raised when agent execution times out"""
    pass

class AgentToolError(AgentException):
    """Raised when a tool execution fails"""
    pass
