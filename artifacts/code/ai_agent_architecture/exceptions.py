"""
Custom exceptions for the AI Agent Architecture system.
"""

from typing import Optional, Any


class AgentArchitectureError(Exception):
    """Base exception for all agent architecture related errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, context: Optional[dict] = None):
        super().__init__(message)
        self.error_code = error_code
        self.context = context or {}
        self.message = message


class CapabilityError(AgentArchitectureError):
    """Raised when there are issues with agent capabilities."""
    pass


class CommunicationError(AgentArchitectureError):
    """Raised when there are communication issues between agents."""
    pass


class MemoryError(AgentArchitectureError):
    """Raised when there are memory system issues."""
    pass


class PlanningError(AgentArchitectureError):
    """Raised when there are planning system issues."""
    pass


class ToolError(AgentArchitectureError):
    """Raised when there are external tool integration issues."""
    pass


class RegistrationError(AgentArchitectureError):
    """Raised when there are registration issues."""
    pass


class ValidationError(AgentArchitectureError):
    """Raised when validation fails."""
    pass


class ConfigurationError(AgentArchitectureError):
    """Raised when there are configuration issues."""
    pass