"""
Advanced Self-Modifying AI Agent Architecture

A production-ready system for building adaptive AI agents with dynamic capabilities,
inter-agent communication, memory systems, and self-modifying planning strategies.

Author: AI Assistant
Version: 1.0.0
License: MIT
"""

from .base_agent import BaseAgent, AgentCapability, CapabilityRegistry
from .communication_bus import CommunicationBus, Message, MessagePriority
from .memory_system import MemorySystem, ShortTermMemory, LongTermMemory
from .adaptive_planner import AdaptivePlanner, PlanningStrategy, Plan, PlanStep
from .external_tools import ToolRegistry, ExternalTool, ToolResult
from .exceptions import (
    AgentArchitectureError,
    CapabilityError,
    CommunicationError,
    MemoryError,
    PlanningError,
    ToolError
)

__version__ = "1.0.0"
__author__ = "AI Assistant"

__all__ = [
    # Core components
    "BaseAgent",
    "CommunicationBus",
    "MemorySystem",
    "AdaptivePlanner",
    "ToolRegistry",
    
    # Supporting classes
    "AgentCapability",
    "CapabilityRegistry",
    "Message",
    "MessagePriority",
    "ShortTermMemory",
    "LongTermMemory",
    "PlanningStrategy",
    "Plan",
    "PlanStep",
    "ExternalTool",
    "ToolResult",
    
    # Exceptions
    "AgentArchitectureError",
    "CapabilityError",
    "CommunicationError",
    "MemoryError",
    "PlanningError",
    "ToolError",
]