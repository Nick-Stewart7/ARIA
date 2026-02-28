"""
Communication Bus for inter-agent messaging with priority queues,
message routing, and delivery guarantees.

This module provides a robust messaging system for agent communication
with features like message persistence, routing, and event-driven delivery.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum, IntEnum
from typing import (
    Any, Dict, List, Optional, Set, Callable, Awaitable,
    Union, Tuple, AsyncGenerator
)
from collections import defaultdict
from asyncio import Queue, Event
import weakref

from .exceptions import CommunicationError, ValidationError


class MessagePriority(IntEnum):
    """Message priority levels (higher number = higher priority)."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class MessageType(Enum):
    """Types of messages in the communication system."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    BROADCAST = "broadcast"
    SYSTEM = "system"


class DeliveryStatus(Enum):
    """Message delivery status."""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    EXPIRED = "expired"
    ACKNOWLEDGED = "acknowledged"


@dataclass
class MessageMetadata:
    """Metadata for messages."""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    delivery_attempts: int = 0
    max_delivery_attempts: int = 3
    requires_acknowledgment: bool = False
    trace_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Check if message has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at


@dataclass
class Message:
    """
    Represents a message in the communication system.
    
    Messages are the primary means of communication between agents,
    supporting various types, priorities, and delivery guarantees.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    recipient_id: Optional[str] = None  # None for broadcast messages
    message_type: MessageType = MessageType.NOTIFICATION
    priority: MessagePriority = MessagePriority.NORMAL
    subject: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    metadata: MessageMetadata = field(default_factory=MessageMetadata)
    status: DeliveryStatus = DeliveryStatus.PENDING
    
    def __post_init__(self):
        """Post-initialization processing."""
        if not self.subject and self.content:
            self.subject = str(self.content.get('subject', 'No Subject'))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'message_type': self.message_type.value,
            'priority': self.priority.value,
            'subject': self.subject,
            'content': self.content,
            'metadata': {
                'created_at': self.metadata.created_at.isoformat(),
                'expires_at': self.metadata.expires_at.isoformat() if self.metadata.expires_at else None,
                'delivery_attempts': self.metadata.delivery_attempts,
                'max_delivery_attempts': self.metadata.max_delivery_attempts,
                'requires_acknowledgment': self.metadata.requires_acknowledgment,
                'trace_id': self.metadata.trace_id,
                'correlation_id': self.metadata.correlation_id,
            },
            'status': self.status.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary."""
        metadata_data = data.get('metadata', {})
        metadata = MessageMetadata(
            created_at=datetime.fromisoformat(metadata_data.get('created_at', datetime.now(timezone.utc).isoformat())),
            expires_at=datetime.fromisoformat(metadata_data['expires_at']) if metadata_data.get('expires_at') else None,
            delivery_attempts=metadata_data.get('delivery_attempts', 0),
            max_delivery_attempts=metadata_data.get('max_delivery_attempts', 3),
            requires_acknowledgment=metadata_data.get('requires_acknowledgment', False),
            trace_id=metadata_data.get('trace_id'),
            correlation_id=metadata_data.get('correlation_id'),
        )
        
        return cls(
            id=data['id'],
            sender_id=data['sender_id'],
            recipient_id=data.get('recipient_id'),
            message_type=MessageType(data['message_type']),
            priority=MessagePriority(data['priority']),
            subject=data['subject'],
            content=data['content'],
            metadata=metadata,
            status=DeliveryStatus(data['status'])
        )
    
    def create_response(self, content: Dict[str, Any], sender_id: str) -> 'Message':
        """Create a response message to this message."""
        return Message(
            sender_id=sender_id,
            recipient_id=self.sender_id,
            message_type=MessageType.RESPONSE,
            priority=self.priority,
            subject=f"Re: {self.subject}",
            content=content,
            metadata=MessageMetadata(
                correlation_id=self.id,
                trace_id=self.metadata.trace_id
            )
        )
    
    def create_acknowledgment(self, sender_id: str) -> 'Message':
        """Create an acknowledgment message."""
        return Message(
            sender_id=sender_id,
            recipient_id=self.sender_id,
            message_type=MessageType.RESPONSE,
            priority=MessagePriority.HIGH,
            subject=f"ACK: {self.subject}",
            content={'acknowledged': True, 'original_message_id': self.id},
            metadata=MessageMetadata(
                correlation_id=self.id,
                trace_id=self.metadata.trace_id
            )
        )


class MessageRouter:
    """
    Routes messages based on recipient patterns and rules.
    """
    
    def __init__(self):
        self.routing_rules: List[Tuple[Callable[[Message], bool], str]] = []
        self.logger = logging.getLogger(f"{__name__}.MessageRouter")
    
    def add_routing_rule(self, condition: Callable[[Message], bool], target: str) -> None:
        """
        Add a routing rule.
        
        Args:
            condition: Function that returns True if message matches rule
            target: Target agent ID or pattern
        """
        self.routing_rules.append((condition, target))
    
    def route_message(self, message: Message) -> List[str]:
        """
        Route a message to appropriate recipients.
        
        Args:
            message: Message to route
            
        Returns:
            List of recipient IDs
        """
        recipients = []
        
        # Direct recipient
        if message.recipient_id:
            recipients.append(message.recipient_id)
        
        # Apply routing rules
        for condition, target in self.routing_rules:
            try:
                if condition(message):
                    recipients.append(target)
            except Exception as e:
                self.logger.error(f"Routing rule failed: {e}")
        
        return list(set(recipients))  # Remove duplicates


class MessageQueue:
    """
    Priority queue for messages with persistence and delivery tracking.
    """
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._queues: Dict[MessagePriority, Queue] = {
            priority: Queue(maxsize=max_size // len(MessagePriority))
            for priority in MessagePriority
        }
        self._message_store: Dict[str, Message] = {}
        self._delivery_tracking: Dict[str, DeliveryStatus] = {}
        self.logger = logging.getLogger(f"{__name__}.MessageQueue")
    
    async def put(self, message: Message) -> None:
        """
        Add a message to the queue.
        
        Args:
            message: Message to add
            
        Raises:
            CommunicationError: If queue is full or message is invalid
        """
        if message.metadata.is_expired():
            raise CommunicationError(f"Message {message.id} has expired")
        
        try:
            queue = self._queues[message.priority]
            await queue.put(message)
            self._message_store[message.id] = message
            self._delivery_tracking[message.id] = DeliveryStatus.PENDING
            
            self.logger.debug(f"Queued message {message.id} with priority {message.priority}")
            
        except asyncio.QueueFull:
            raise CommunicationError(f"Message queue is full (priority: {message.priority})")
    
    async def get(self, timeout: Optional[float] = None) -> Message:
        """
        Get the highest priority message from the queue.
        
        Args:
            timeout: Maximum time to wait for a message
            
        Returns:
            The next message in priority order
            
        Raises:
            CommunicationError: If timeout occurs or queue is empty
        """
        # Try higher priority queues first
        for priority in sorted(MessagePriority, reverse=True):
            queue = self._queues[priority]
            if not queue.empty():
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=0.1)
                    return message
                except asyncio.TimeoutError:
                    continue
        
        # If no high priority messages, wait for any message
        tasks = [
            asyncio.create_task(queue.get())
            for queue in self._queues.values()
            if not queue.empty()
        ]
        
        if not tasks:
            # All queues empty, wait for any new message
            tasks = [
                asyncio.create_task(queue.get())
                for queue in self._queues.values()
            ]
        
        try:
            done, pending = await asyncio.wait_for(
                asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED),
                timeout=timeout
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
            
            # Get result from completed task
            message = done.pop().result()
            return message
            
        except asyncio.TimeoutError:
            for task in tasks:
                task.cancel()
            raise CommunicationError("Message queue timeout")
    
    def get_message(self, message_id: str) -> Optional[Message]:
        """Get a message by ID."""
        return self._message_store.get(message_id)
    
    def update_delivery_status(self, message_id: str, status: DeliveryStatus) -> None:
        """Update message delivery status."""
        if message_id in self._delivery_tracking:
            self._delivery_tracking[message_id] = status
            if message_id in self._message_store:
                self._message_store[message_id].status = status
    
    def get_delivery_status(self, message_id: str) -> Optional[DeliveryStatus]:
        """Get message delivery status."""
        return self._delivery_tracking.get(message_id)
    
    def cleanup_expired_messages(self) -> int:
        """Remove expired messages and return count of removed messages."""
        expired_count = 0
        expired_ids = []
        
        for message_id, message in self._message_store.items():
            if message.metadata.is_expired():
                expired_ids.append(message_id)
                expired_count += 1
        
        for message_id in expired_ids:
            self._message_store.pop(message_id, None)
            self._delivery_tracking.pop(message_id, None)
            # Note: Messages in queues will be checked when retrieved
        
        return expired_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return {
            'total_messages': len(self._message_store),
            'pending_messages': sum(1 for s in self._delivery_tracking.values() if s == DeliveryStatus.PENDING),
            'delivered_messages': sum(1 for s in self._delivery_tracking.values() if s == DeliveryStatus.DELIVERED),
            'failed_messages': sum(1 for s in self._delivery_tracking.values() if s == DeliveryStatus.FAILED),
            'queue_sizes': {str(p): q.qsize() for p, q in self._queues.items()}
        }


class CommunicationBus:
    """
    Central communication hub for inter-agent messaging.
    
    Provides reliable message delivery, routing, persistence,
    and event-driven communication patterns.
    """
    
    def __init__(self, max_queue_size: int = 10000, cleanup_interval: int = 300):
        self.max_queue_size = max_queue_size
        self.cleanup_interval = cleanup_interval
        
        # Core components
        self.message_queues: Dict[str, MessageQueue] = {}
        self.router = MessageRouter()
        self.subscribers: Dict[str, Set[str]] = defaultdict(set)  # topic -> agent_ids
        self.agent_refs: Dict[str, Any] = {}  # agent_id -> weak reference
        
        # Event handling
        self.message_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Statistics
        self.stats = {
            'messages_sent': 0,
            'messages_delivered': 0,
            'messages_failed': 0,
            'broadcasts_sent': 0
        }
        
        self.logger = logging.getLogger(f"{__name__}.CommunicationBus")
    
    async def start(self) -> None:
        """Start the communication bus."""
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.logger.info("Communication bus started")
    
    async def stop(self) -> None:
        """Stop the communication bus."""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Communication bus stopped")
    
    def register_agent(self, agent_id: str, agent_ref: Any = None) -> None:
        """
        Register an agent with the communication bus.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_ref: Weak reference to the agent (optional)
        """
        if agent_id not in self.message_queues:
            self.message_queues[agent_id] = MessageQueue(self.max_queue_size)
        
        if agent_ref:
            self.agent_refs[agent_id] = weakref.ref(agent_ref)
        
        self.logger.info(f"Registered agent: {agent_id}")
    
    def unregister_agent(self, agent_id: str) -> None:
        """
        Unregister an agent from the communication bus.
        
        Args:
            agent_id: Agent identifier to unregister
        """
        self.message_queues.pop(agent_id, None)
        self.agent_refs.pop(agent_id, None)
        
        # Remove from all subscriptions
        for topic_agents in self.subscribers.values():
            topic_agents.discard(agent_id)
        
        self.logger.info(f"Unregistered agent: {agent_id}")
    
    async def send_message(self, message: Message) -> bool:
        """
        Send a message through the communication bus.
        
        Args:
            message: Message to send
            
        Returns:
            True if message was queued successfully
            
        Raises:
            CommunicationError: If message sending fails
        """
        try:
            # Route message to determine recipients
            recipients = self.router.route_message(message)
            
            if message.recipient_id and message.recipient_id not in recipients:
                recipients.append(message.recipient_id)
            
            if not recipients:
                raise CommunicationError(f"No recipients found for message {message.id}")
            
            # Send to each recipient
            success_count = 0
            for recipient_id in recipients:
                if recipient_id not in self.message_queues:
                    self.logger.warning(f"Recipient {recipient_id} not registered")
                    continue
                
                try:
                    # Create a copy for each recipient
                    message_copy = Message(
                        id=str(uuid.uuid4()),
                        sender_id=message.sender_id,
                        recipient_id=recipient_id,
                        message_type=message.message_type,
                        priority=message.priority,
                        subject=message.subject,
                        content=message.content.copy(),
                        metadata=message.metadata,
                        status=DeliveryStatus.PENDING
                    )
                    
                    await self.message_queues[recipient_id].put(message_copy)
                    success_count += 1
                    
                    # Notify message handlers
                    await self._notify_message_handlers('message_sent', message_copy)
                    
                except Exception as e:
                    self.logger.error(f"Failed to send message to {recipient_id}: {e}")
            
            self.stats['messages_sent'] += success_count
            
            if success_count == 0:
                raise CommunicationError("Failed to deliver message to any recipient")
            
            return True
            
        except Exception as e:
            self.stats['messages_failed'] += 1
            self.logger.error(f"Message sending failed: {e}")
            raise CommunicationError(f"Failed to send message: {e}") from e
    
    async def receive_message(self, agent_id: str, timeout: Optional[float] = None) -> Message:
        """
        Receive a message for an agent.
        
        Args:
            agent_id: Agent identifier
            timeout: Maximum time to wait for a message
            
        Returns:
            The next message for the agent
            
        Raises:
            CommunicationError: If agent not registered or timeout occurs
        """
        if agent_id not in self.message_queues:
            raise CommunicationError(f"Agent {agent_id} not registered")
        
        try:
            message = await self.message_queues[agent_id].get(timeout)
            
            # Update delivery status
            self.message_queues[agent_id].update_delivery_status(
                message.id, DeliveryStatus.DELIVERED
            )
            
            self.stats['messages_delivered'] += 1
            
            # Send acknowledgment if required
            if message.metadata.requires_acknowledgment:
                ack_message = message.create_acknowledgment(agent_id)
                await self.send_message(ack_message)
            
            # Notify handlers
            await self._notify_message_handlers('message_received', message)
            
            return message
            
        except Exception as e:
            self.stats['messages_failed'] += 1
            raise CommunicationError(f"Failed to receive message: {e}") from e
    
    async def broadcast_message(self, message: Message, topic: Optional[str] = None) -> int:
        """
        Broadcast a message to all agents or subscribers to a topic.
        
        Args:
            message: Message to broadcast
            topic: Topic to broadcast to (None for all agents)
            
        Returns:
            Number of agents the message was sent to
        """
        message.message_type = MessageType.BROADCAST
        message.recipient_id = None
        
        if topic:
            recipients = list(self.subscribers.get(topic, set()))
        else:
            recipients = list(self.message_queues.keys())
        
        sent_count = 0
        for agent_id in recipients:
            try:
                message_copy = Message(
                    id=str(uuid.uuid4()),
                    sender_id=message.sender_id,
                    recipient_id=agent_id,
                    message_type=MessageType.BROADCAST,
                    priority=message.priority,
                    subject=message.subject,
                    content=message.content.copy(),
                    metadata=message.metadata,
                    status=DeliveryStatus.PENDING
                )
                
                await self.message_queues[agent_id].put(message_copy)
                sent_count += 1
                
            except Exception as e:
                self.logger.error(f"Failed to broadcast to {agent_id}: {e}")
        
        self.stats['broadcasts_sent'] += 1
        self.logger.info(f"Broadcast message sent to {sent_count} agents")
        
        return sent_count
    
    def subscribe(self, agent_id: str, topic: str) -> None:
        """Subscribe an agent to a topic."""
        self.subscribers[topic].add(agent_id)
        self.logger.debug(f"Agent {agent_id} subscribed to topic {topic}")
    
    def unsubscribe(self, agent_id: str, topic: str) -> None:
        """Unsubscribe an agent from a topic."""
        self.subscribers[topic].discard(agent_id)
        self.logger.debug(f"Agent {agent_id} unsubscribed from topic {topic}")
    
    def add_message_handler(self, event_type: str, handler: Callable) -> None:
        """Add a message event handler."""
        self.message_handlers[event_type].append(handler)
    
    def get_queue_stats(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get queue statistics for an agent."""
        if agent_id in self.message_queues:
            return self.message_queues[agent_id].get_stats()
        return None
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global communication bus statistics."""
        return {
            **self.stats,
            'registered_agents': len(self.message_queues),
            'active_topics': len([t for t, subs in self.subscribers.items() if subs]),
            'total_subscriptions': sum(len(subs) for subs in self.subscribers.values())
        }
    
    async def _cleanup_loop(self) -> None:
        """Background task for cleaning up expired messages."""
        while self._running:
            try:
                total_cleaned = 0
                for queue in self.message_queues.values():
                    cleaned = queue.cleanup_expired_messages()
                    total_cleaned += cleaned
                
                if total_cleaned > 0:
                    self.logger.info(f"Cleaned up {total_cleaned} expired messages")
                
                await asyncio.sleep(self.cleanup_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _notify_message_handlers(self, event_type: str, message: Message) -> None:
        """Notify message event handlers."""
        for handler in self.message_handlers[event_type]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, message)
                else:
                    handler(event_type, message)
            except Exception as e:
                self.logger.error(f"Message handler failed for {event_type}: {e}")
    
    def __repr__(self) -> str:
        return f"<CommunicationBus(agents={len(self.message_queues)}, topics={len(self.subscribers)})>"