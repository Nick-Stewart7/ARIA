"""
Base Agent class with dynamic capability registration system.

This module provides the foundation for creating adaptive AI agents with
dynamic capability management, event handling, and lifecycle management.
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import (
    Any, Dict, List, Optional, Set, Callable, Awaitable, 
    TypeVar, Generic, Union, Protocol
)
from weakref import WeakSet

from .exceptions import CapabilityError, RegistrationError, ValidationError


# Type variables and protocols
T = TypeVar('T')
CapabilityResult = TypeVar('CapabilityResult')


class CapabilityProtocol(Protocol):
    """Protocol for agent capabilities."""
    
    async def execute(self, agent: 'BaseAgent', *args, **kwargs) -> Any:
        """Execute the capability."""
        ...
    
    def validate_input(self, *args, **kwargs) -> bool:
        """Validate input parameters."""
        ...


class CapabilityPriority(Enum):
    """Priority levels for capability execution."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class CapabilityStatus(Enum):
    """Status of capability registration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DEPRECATED = "deprecated"


@dataclass
class CapabilityMetadata:
    """Metadata for agent capabilities."""
    name: str
    version: str
    description: str
    priority: CapabilityPriority = CapabilityPriority.NORMAL
    dependencies: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_used: Optional[datetime] = None
    use_count: int = 0
    error_count: int = 0


class AgentCapability(ABC, Generic[CapabilityResult]):
    """
    Abstract base class for agent capabilities.
    
    Capabilities are modular units of functionality that can be dynamically
    registered and executed by agents.
    """
    
    def __init__(self, metadata: CapabilityMetadata):
        self.metadata = metadata
        self.status = CapabilityStatus.ACTIVE
        self.logger = logging.getLogger(f"{__name__}.{metadata.name}")
    
    @abstractmethod
    async def execute(self, agent: 'BaseAgent', *args, **kwargs) -> CapabilityResult:
        """
        Execute the capability.
        
        Args:
            agent: The agent executing this capability
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            The result of capability execution
            
        Raises:
            CapabilityError: If execution fails
        """
        pass
    
    def validate_input(self, *args, **kwargs) -> bool:
        """
        Validate input parameters.
        
        Returns:
            True if input is valid, False otherwise
        """
        return True
    
    async def pre_execute(self, agent: 'BaseAgent', *args, **kwargs) -> None:
        """Hook called before capability execution."""
        self.metadata.use_count += 1
        self.metadata.last_used = datetime.now(timezone.utc)
    
    async def post_execute(self, agent: 'BaseAgent', result: CapabilityResult, *args, **kwargs) -> None:
        """Hook called after successful capability execution."""
        pass
    
    async def on_error(self, agent: 'BaseAgent', error: Exception, *args, **kwargs) -> None:
        """Hook called when capability execution fails."""
        self.metadata.error_count += 1
        self.logger.error(f"Capability {self.metadata.name} failed: {error}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert capability to dictionary representation."""
        return {
            'name': self.metadata.name,
            'version': self.metadata.version,
            'description': self.metadata.description,
            'priority': self.metadata.priority.value,
            'status': self.status.value,
            'dependencies': self.metadata.dependencies,
            'tags': list(self.metadata.tags),
            'created_at': self.metadata.created_at.isoformat(),
            'last_used': self.metadata.last_used.isoformat() if self.metadata.last_used else None,
            'use_count': self.metadata.use_count,
            'error_count': self.metadata.error_count
        }


class CapabilityRegistry:
    """
    Registry for managing agent capabilities with dependency resolution
    and lifecycle management.
    """
    
    def __init__(self):
        self._capabilities: Dict[str, AgentCapability] = {}
        self._dependency_graph: Dict[str, Set[str]] = {}
        self._observers: WeakSet = WeakSet()
        self.logger = logging.getLogger(f"{__name__}.CapabilityRegistry")
    
    def register(self, capability: AgentCapability) -> None:
        """
        Register a new capability.
        
        Args:
            capability: The capability to register
            
        Raises:
            RegistrationError: If registration fails
            ValidationError: If capability validation fails
        """
        name = capability.metadata.name
        
        # Validate capability
        if not self._validate_capability(capability):
            raise ValidationError(f"Capability {name} failed validation")
        
        # Check for dependency cycles
        if self._would_create_cycle(name, capability.metadata.dependencies):
            raise RegistrationError(f"Registering {name} would create dependency cycle")
        
        # Register capability
        self._capabilities[name] = capability
        self._dependency_graph[name] = set(capability.metadata.dependencies)
        
        # Notify observers
        self._notify_observers('capability_registered', capability)
        
        self.logger.info(f"Registered capability: {name} v{capability.metadata.version}")
    
    def unregister(self, name: str) -> Optional[AgentCapability]:
        """
        Unregister a capability.
        
        Args:
            name: Name of the capability to unregister
            
        Returns:
            The unregistered capability, or None if not found
        """
        capability = self._capabilities.pop(name, None)
        if capability:
            self._dependency_graph.pop(name, None)
            # Remove from other capabilities' dependencies
            for deps in self._dependency_graph.values():
                deps.discard(name)
            
            self._notify_observers('capability_unregistered', capability)
            self.logger.info(f"Unregistered capability: {name}")
        
        return capability
    
    def get(self, name: str) -> Optional[AgentCapability]:
        """Get a capability by name."""
        return self._capabilities.get(name)
    
    def list_capabilities(self, status: Optional[CapabilityStatus] = None, 
                         tags: Optional[Set[str]] = None) -> List[AgentCapability]:
        """
        List capabilities with optional filtering.
        
        Args:
            status: Filter by capability status
            tags: Filter by tags (capabilities must have all specified tags)
            
        Returns:
            List of matching capabilities
        """
        capabilities = list(self._capabilities.values())
        
        if status:
            capabilities = [c for c in capabilities if c.status == status]
        
        if tags:
            capabilities = [c for c in capabilities if tags.issubset(c.metadata.tags)]
        
        return capabilities
    
    def get_execution_order(self, capability_names: List[str]) -> List[str]:
        """
        Get execution order for capabilities based on dependencies.
        
        Args:
            capability_names: List of capability names to order
            
        Returns:
            List of capability names in execution order
            
        Raises:
            CapabilityError: If circular dependencies detected
        """
        if not capability_names:
            return []
        
        # Topological sort
        in_degree = {name: 0 for name in capability_names}
        for name in capability_names:
            for dep in self._dependency_graph.get(name, set()):
                if dep in in_degree:
                    in_degree[dep] += 1
        
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            for name in capability_names:
                if current in self._dependency_graph.get(name, set()):
                    in_degree[name] -= 1
                    if in_degree[name] == 0:
                        queue.append(name)
        
        if len(result) != len(capability_names):
            raise CapabilityError("Circular dependency detected in capabilities")
        
        return result
    
    def _validate_capability(self, capability: AgentCapability) -> bool:
        """Validate a capability before registration."""
        if not capability.metadata.name:
            return False
        if not capability.metadata.version:
            return False
        return True
    
    def _would_create_cycle(self, name: str, dependencies: List[str]) -> bool:
        """Check if adding dependencies would create a cycle."""
        # Simple cycle detection - can be enhanced
        visited = set()
        
        def has_path_to(from_node: str, to_node: str) -> bool:
            if from_node == to_node:
                return True
            if from_node in visited:
                return False
            
            visited.add(from_node)
            for dep in self._dependency_graph.get(from_node, set()):
                if has_path_to(dep, to_node):
                    return True
            return False
        
        for dep in dependencies:
            if dep in self._capabilities and has_path_to(dep, name):
                return True
        
        return False
    
    def add_observer(self, observer: Callable[[str, AgentCapability], None]) -> None:
        """Add an observer for capability events."""
        self._observers.add(observer)
    
    def _notify_observers(self, event: str, capability: AgentCapability) -> None:
        """Notify observers of capability events."""
        for observer in self._observers:
            try:
                observer(event, capability)
            except Exception as e:
                self.logger.error(f"Observer notification failed: {e}")


class BaseAgent(ABC):
    """
    Base class for AI agents with dynamic capability management.
    
    Provides core functionality for capability registration, execution,
    event handling, and lifecycle management.
    """
    
    def __init__(self, agent_id: Optional[str] = None, name: Optional[str] = None):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.name = name or f"Agent-{self.agent_id[:8]}"
        self.created_at = datetime.now(timezone.utc)
        self.last_active = self.created_at
        self.is_active = False
        
        # Core components
        self.capability_registry = CapabilityRegistry()
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.context: Dict[str, Any] = {}
        self.metrics: Dict[str, Any] = {
            'capabilities_executed': 0,
            'errors_encountered': 0,
            'total_runtime': 0.0
        }
        
        # Logging
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}.{self.agent_id[:8]}")
        
        # Setup capability registry observer
        self.capability_registry.add_observer(self._on_capability_event)
    
    async def start(self) -> None:
        """Start the agent."""
        self.is_active = True
        self.last_active = datetime.now(timezone.utc)
        await self.on_start()
        self.emit_event('agent_started', {'agent_id': self.agent_id})
        self.logger.info(f"Agent {self.name} started")
    
    async def stop(self) -> None:
        """Stop the agent."""
        self.is_active = False
        await self.on_stop()
        self.emit_event('agent_stopped', {'agent_id': self.agent_id})
        self.logger.info(f"Agent {self.name} stopped")
    
    async def execute_capability(self, capability_name: str, *args, **kwargs) -> Any:
        """
        Execute a capability by name.
        
        Args:
            capability_name: Name of the capability to execute
            *args: Positional arguments for capability
            **kwargs: Keyword arguments for capability
            
        Returns:
            Result of capability execution
            
        Raises:
            CapabilityError: If capability not found or execution fails
        """
        capability = self.capability_registry.get(capability_name)
        if not capability:
            raise CapabilityError(f"Capability '{capability_name}' not found")
        
        if capability.status != CapabilityStatus.ACTIVE:
            raise CapabilityError(f"Capability '{capability_name}' is not active")
        
        # Validate input
        if not capability.validate_input(*args, **kwargs):
            raise CapabilityError(f"Invalid input for capability '{capability_name}'")
        
        start_time = datetime.now(timezone.utc)
        
        try:
            # Execute capability hooks and main execution
            await capability.pre_execute(self, *args, **kwargs)
            result = await capability.execute(self, *args, **kwargs)
            await capability.post_execute(self, result, *args, **kwargs)
            
            # Update metrics
            self.metrics['capabilities_executed'] += 1
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.metrics['total_runtime'] += execution_time
            
            # Emit success event
            self.emit_event('capability_executed', {
                'capability': capability_name,
                'execution_time': execution_time,
                'success': True
            })
            
            self.logger.debug(f"Executed capability {capability_name} in {execution_time:.3f}s")
            return result
            
        except Exception as e:
            await capability.on_error(self, e, *args, **kwargs)
            self.metrics['errors_encountered'] += 1
            
            # Emit error event
            self.emit_event('capability_error', {
                'capability': capability_name,
                'error': str(e),
                'success': False
            })
            
            self.logger.error(f"Capability {capability_name} failed: {e}")
            raise CapabilityError(f"Capability execution failed: {e}") from e
    
    def register_capability(self, capability: AgentCapability) -> None:
        """Register a new capability."""
        self.capability_registry.register(capability)
    
    def unregister_capability(self, name: str) -> Optional[AgentCapability]:
        """Unregister a capability."""
        return self.capability_registry.unregister(name)
    
    def has_capability(self, name: str) -> bool:
        """Check if agent has a specific capability."""
        return self.capability_registry.get(name) is not None
    
    def list_capabilities(self, **filters) -> List[AgentCapability]:
        """List agent capabilities with optional filtering."""
        return self.capability_registry.list_capabilities(**filters)
    
    def add_event_handler(self, event_type: str, handler: Callable) -> None:
        """Add an event handler."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def remove_event_handler(self, event_type: str, handler: Callable) -> None:
        """Remove an event handler."""
        if event_type in self.event_handlers:
            try:
                self.event_handlers[event_type].remove(handler)
            except ValueError:
                pass
    
    def emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit an event to all registered handlers."""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        asyncio.create_task(handler(event_type, data))
                    else:
                        handler(event_type, data)
                except Exception as e:
                    self.logger.error(f"Event handler failed for {event_type}: {e}")
    
    def update_context(self, **kwargs) -> None:
        """Update agent context."""
        self.context.update(kwargs)
        self.last_active = datetime.now(timezone.utc)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics."""
        return {
            **self.metrics,
            'uptime': (datetime.now(timezone.utc) - self.created_at).total_seconds(),
            'capabilities_count': len(self.capability_registry._capabilities),
            'is_active': self.is_active
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary representation."""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'last_active': self.last_active.isoformat(),
            'is_active': self.is_active,
            'capabilities': [cap.to_dict() for cap in self.list_capabilities()],
            'metrics': self.get_metrics(),
            'context_keys': list(self.context.keys())
        }
    
    # Abstract methods for subclasses to implement
    @abstractmethod
    async def on_start(self) -> None:
        """Called when agent starts."""
        pass
    
    @abstractmethod
    async def on_stop(self) -> None:
        """Called when agent stops."""
        pass
    
    # Private methods
    def _on_capability_event(self, event: str, capability: AgentCapability) -> None:
        """Handle capability registry events."""
        self.emit_event(f'capability_{event}', {
            'capability_name': capability.metadata.name,
            'capability_version': capability.metadata.version
        })
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.agent_id[:8]}, name={self.name})>"