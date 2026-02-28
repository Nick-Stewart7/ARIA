"""
Memory Manager - Three-Tier Memory Architecture Implementation
==============================================================

This module implements a memory management system based on the three-tier
cognitive architecture:
- Episodic Memory: Specific events and experiences with temporal context
- Semantic Memory: General knowledge and facts without temporal context  
- Procedural Memory: Skills, procedures, and how-to knowledge

Features:
- JSON-based persistence for all memory types
- Timestamp tracking for episodic memories
- Category-based organization for semantic memories
- Step-based storage for procedural memories
- Search and retrieval capabilities across all memory types
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class EpisodicMemory:
    """Represents a specific event or experience with temporal context."""
    id: str
    event: str
    context: Dict[str, Any]
    timestamp: str
    emotional_weight: float = 0.0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class SemanticMemory:
    """Represents general knowledge and facts."""
    id: str
    concept: str
    description: str
    category: str
    attributes: Dict[str, Any]
    confidence: float = 1.0
    related_concepts: List[str] = None
    
    def __post_init__(self):
        if self.related_concepts is None:
            self.related_concepts = []


@dataclass
class ProceduralMemory:
    """Represents skills, procedures, and how-to knowledge."""
    id: str
    name: str
    description: str
    steps: List[Dict[str, str]]
    skill_level: str = "beginner"  # beginner, intermediate, advanced
    prerequisites: List[str] = None
    success_rate: float = 0.0
    
    def __post_init__(self):
        if self.prerequisites is None:
            self.prerequisites = []


class MemoryManager:
    """
    Three-tier memory management system implementing episodic, semantic, 
    and procedural memory with JSON-based persistence.
    """
    
    def __init__(self, storage_dir: str = "memory_storage"):
        """
        Initialize the Memory Manager.
        
        Args:
            storage_dir: Directory to store memory files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # Memory storage dictionaries
        self.episodic_memories: Dict[str, EpisodicMemory] = {}
        self.semantic_memories: Dict[str, SemanticMemory] = {}
        self.procedural_memories: Dict[str, ProceduralMemory] = {}
        
        # File paths for persistence
        self.episodic_file = self.storage_dir / "episodic_memory.json"
        self.semantic_file = self.storage_dir / "semantic_memory.json"
        self.procedural_file = self.storage_dir / "procedural_memory.json"
        
        # Load existing memories
        self.load_all_memories()
    
    # =================== EPISODIC MEMORY METHODS ===================
    
    def store_episodic_memory(self, memory_id: str, event: str, 
                            context: Dict[str, Any], 
                            emotional_weight: float = 0.0,
                            tags: List[str] = None) -> EpisodicMemory:
        """
        Store a new episodic memory (specific event with temporal context).
        
        Args:
            memory_id: Unique identifier for the memory
            event: Description of the event
            context: Contextual information about the event
            emotional_weight: Emotional significance (-1.0 to 1.0)
            tags: List of tags for categorization
        
        Returns:
            EpisodicMemory object that was stored
        """
        timestamp = datetime.now().isoformat()
        memory = EpisodicMemory(
            id=memory_id,
            event=event,
            context=context,
            timestamp=timestamp,
            emotional_weight=emotional_weight,
            tags=tags or []
        )
        
        self.episodic_memories[memory_id] = memory
        self._save_episodic_memories()
        return memory
    
    def retrieve_episodic_memory(self, memory_id: str) -> Optional[EpisodicMemory]:
        """Retrieve a specific episodic memory by ID."""
        return self.episodic_memories.get(memory_id)
    
    def search_episodic_memories(self, query: str = None, 
                               tags: List[str] = None,
                               start_date: str = None,
                               end_date: str = None) -> List[EpisodicMemory]:
        """
        Search episodic memories based on various criteria.
        
        Args:
            query: Text to search for in event descriptions
            tags: List of tags to filter by
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
        
        Returns:
            List of matching EpisodicMemory objects
        """
        results = []
        
        for memory in self.episodic_memories.values():
            matches = True
            
            # Text search
            if query and query.lower() not in memory.event.lower():
                matches = False
            
            # Tag filtering
            if tags and not any(tag in memory.tags for tag in tags):
                matches = False
            
            # Date filtering
            if start_date and memory.timestamp < start_date:
                matches = False
            if end_date and memory.timestamp > end_date:
                matches = False
            
            if matches:
                results.append(memory)
        
        # Sort by timestamp (most recent first)
        return sorted(results, key=lambda m: m.timestamp, reverse=True)
    
    # =================== SEMANTIC MEMORY METHODS ===================
    
    def store_semantic_memory(self, memory_id: str, concept: str, 
                            description: str, category: str,
                            attributes: Dict[str, Any] = None,
                            confidence: float = 1.0,
                            related_concepts: List[str] = None) -> SemanticMemory:
        """
        Store semantic memory (general knowledge/facts).
        
        Args:
            memory_id: Unique identifier
            concept: The concept or fact being stored
            description: Detailed description
            category: Category for organization
            attributes: Additional attributes
            confidence: Confidence level (0.0 to 1.0)
            related_concepts: List of related concept IDs
        
        Returns:
            SemanticMemory object that was stored
        """
        memory = SemanticMemory(
            id=memory_id,
            concept=concept,
            description=description,
            category=category,
            attributes=attributes or {},
            confidence=confidence,
            related_concepts=related_concepts or []
        )
        
        self.semantic_memories[memory_id] = memory
        self._save_semantic_memories()
        return memory
    
    def retrieve_semantic_memory(self, memory_id: str) -> Optional[SemanticMemory]:
        """Retrieve a specific semantic memory by ID."""
        return self.semantic_memories.get(memory_id)
    
    def search_semantic_memories(self, query: str = None,
                               category: str = None,
                               min_confidence: float = 0.0) -> List[SemanticMemory]:
        """
        Search semantic memories.
        
        Args:
            query: Text to search for in concept/description
            category: Category to filter by
            min_confidence: Minimum confidence level
        
        Returns:
            List of matching SemanticMemory objects
        """
        results = []
        
        for memory in self.semantic_memories.values():
            matches = True
            
            # Text search
            if query:
                query_lower = query.lower()
                if (query_lower not in memory.concept.lower() and 
                    query_lower not in memory.description.lower()):
                    matches = False
            
            # Category filtering
            if category and memory.category != category:
                matches = False
            
            # Confidence filtering
            if memory.confidence < min_confidence:
                matches = False
            
            if matches:
                results.append(memory)
        
        # Sort by confidence (highest first)
        return sorted(results, key=lambda m: m.confidence, reverse=True)
    
    def get_semantic_categories(self) -> List[str]:
        """Get all unique categories in semantic memory."""
        return list(set(memory.category for memory in self.semantic_memories.values()))
    
    # =================== PROCEDURAL MEMORY METHODS ===================
    
    def store_procedural_memory(self, memory_id: str, name: str,
                              description: str, steps: List[Dict[str, str]],
                              skill_level: str = "beginner",
                              prerequisites: List[str] = None,
                              success_rate: float = 0.0) -> ProceduralMemory:
        """
        Store procedural memory (skills/procedures).
        
        Args:
            memory_id: Unique identifier
            name: Name of the procedure/skill
            description: Description of what this procedure does
            steps: List of steps, each with 'action' and 'description' keys
            skill_level: beginner, intermediate, or advanced
            prerequisites: List of prerequisite procedure IDs
            success_rate: Success rate (0.0 to 1.0)
        
        Returns:
            ProceduralMemory object that was stored
        """
        memory = ProceduralMemory(
            id=memory_id,
            name=name,
            description=description,
            steps=steps,
            skill_level=skill_level,
            prerequisites=prerequisites or [],
            success_rate=success_rate
        )
        
        self.procedural_memories[memory_id] = memory
        self._save_procedural_memories()
        return memory
    
    def retrieve_procedural_memory(self, memory_id: str) -> Optional[ProceduralMemory]:
        """Retrieve a specific procedural memory by ID."""
        return self.procedural_memories.get(memory_id)
    
    def search_procedural_memories(self, query: str = None,
                                 skill_level: str = None,
                                 min_success_rate: float = 0.0) -> List[ProceduralMemory]:
        """
        Search procedural memories.
        
        Args:
            query: Text to search for in name/description
            skill_level: Skill level to filter by
            min_success_rate: Minimum success rate
        
        Returns:
            List of matching ProceduralMemory objects
        """
        results = []
        
        for memory in self.procedural_memories.values():
            matches = True
            
            # Text search
            if query:
                query_lower = query.lower()
                if (query_lower not in memory.name.lower() and 
                    query_lower not in memory.description.lower()):
                    matches = False
            
            # Skill level filtering
            if skill_level and memory.skill_level != skill_level:
                matches = False
            
            # Success rate filtering
            if memory.success_rate < min_success_rate:
                matches = False
            
            if matches:
                results.append(memory)
        
        # Sort by success rate (highest first)
        return sorted(results, key=lambda m: m.success_rate, reverse=True)
    
    def update_procedure_success_rate(self, memory_id: str, new_rate: float):
        """Update the success rate of a procedural memory."""
        if memory_id in self.procedural_memories:
            self.procedural_memories[memory_id].success_rate = new_rate
            self._save_procedural_memories()
    
    # =================== UTILITY AND PERSISTENCE METHODS ===================
    
    def get_memory_stats(self) -> Dict[str, int]:
        """Get statistics about stored memories."""
        return {
            "episodic_count": len(self.episodic_memories),
            "semantic_count": len(self.semantic_memories),
            "procedural_count": len(self.procedural_memories),
            "total_memories": (len(self.episodic_memories) + 
                             len(self.semantic_memories) + 
                             len(self.procedural_memories))
        }
    
    def clear_all_memories(self):
        """Clear all memories from storage (use with caution!)."""
        self.episodic_memories.clear()
        self.semantic_memories.clear()
        self.procedural_memories.clear()
        self._save_all_memories()
    
    def delete_memory(self, memory_type: str, memory_id: str) -> bool:
        """
        Delete a specific memory.
        
        Args:
            memory_type: 'episodic', 'semantic', or 'procedural'
            memory_id: ID of the memory to delete
        
        Returns:
            True if memory was deleted, False if not found
        """
        if memory_type == "episodic" and memory_id in self.episodic_memories:
            del self.episodic_memories[memory_id]
            self._save_episodic_memories()
            return True
        elif memory_type == "semantic" and memory_id in self.semantic_memories:
            del self.semantic_memories[memory_id]
            self._save_semantic_memories()
            return True
        elif memory_type == "procedural" and memory_id in self.procedural_memories:
            del self.procedural_memories[memory_id]
            self._save_procedural_memories()
            return True
        return False
    
    # =================== PRIVATE PERSISTENCE METHODS ===================
    
    def _save_episodic_memories(self):
        """Save episodic memories to JSON file."""
        data = {mid: asdict(memory) for mid, memory in self.episodic_memories.items()}
        with open(self.episodic_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_semantic_memories(self):
        """Save semantic memories to JSON file."""
        data = {mid: asdict(memory) for mid, memory in self.semantic_memories.items()}
        with open(self.semantic_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_procedural_memories(self):
        """Save procedural memories to JSON file."""
        data = {mid: asdict(memory) for mid, memory in self.procedural_memories.items()}
        with open(self.procedural_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_all_memories(self):
        """Save all memory types to their respective files."""
        self._save_episodic_memories()
        self._save_semantic_memories()
        self._save_procedural_memories()
    
    def load_all_memories(self):
        """Load all memories from JSON files."""
        # Load episodic memories
        if self.episodic_file.exists():
            with open(self.episodic_file, 'r') as f:
                data = json.load(f)
                self.episodic_memories = {
                    mid: EpisodicMemory(**memory_data) 
                    for mid, memory_data in data.items()
                }
        
        # Load semantic memories
        if self.semantic_file.exists():
            with open(self.semantic_file, 'r') as f:
                data = json.load(f)
                self.semantic_memories = {
                    mid: SemanticMemory(**memory_data) 
                    for mid, memory_data in data.items()
                }
        
        # Load procedural memories
        if self.procedural_file.exists():
            with open(self.procedural_file, 'r') as f:
                data = json.load(f)
                self.procedural_memories = {
                    mid: ProceduralMemory(**memory_data) 
                    for mid, memory_data in data.items()
                }
    
    def export_memories(self, export_path: str = "memory_export.json") -> str:
        """
        Export all memories to a single JSON file.
        
        Args:
            export_path: Path for the export file
        
        Returns:
            Path to the exported file
        """
        export_data = {
            "episodic": {mid: asdict(memory) for mid, memory in self.episodic_memories.items()},
            "semantic": {mid: asdict(memory) for mid, memory in self.semantic_memories.items()},
            "procedural": {mid: asdict(memory) for mid, memory in self.procedural_memories.items()},
            "export_timestamp": datetime.now().isoformat(),
            "stats": self.get_memory_stats()
        }
        
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return export_path


# =================== USAGE EXAMPLES ===================

if __name__ == "__main__":
    # Example usage of the Memory Manager
    
    # Initialize memory manager
    mm = MemoryManager("example_memory")
    
    # Store episodic memory (specific event)
    mm.store_episodic_memory(
        "meeting_001",
        "Team meeting about project Alpha",
        {
            "location": "Conference Room A",
            "attendees": ["Alice", "Bob", "Charlie"],
            "duration": "2 hours",
            "outcomes": ["Decided on architecture", "Set deadlines"]
        },
        emotional_weight=0.3,
        tags=["work", "meeting", "project-alpha"]
    )
    
    # Store semantic memory (general knowledge)
    mm.store_semantic_memory(
        "python_basics",
        "Python Programming Language",
        "Python is a high-level, interpreted programming language known for its simplicity and readability.",
        "Programming Languages",
        {
            "created": 1991,
            "creator": "Guido van Rossum",
            "paradigms": ["object-oriented", "functional", "procedural"]
        },
        confidence=0.95,
        related_concepts=["programming", "software-development"]
    )
    
    # Store procedural memory (how-to knowledge)
    mm.store_procedural_memory(
        "make_coffee",
        "How to Make Coffee",
        "Step-by-step process for brewing coffee using a French press",
        [
            {"action": "Heat water", "description": "Heat water to 200°F (93°C)"},
            {"action": "Grind coffee", "description": "Coarsely grind coffee beans"},
            {"action": "Add coffee", "description": "Add coffee grounds to French press"},
            {"action": "Pour water", "description": "Pour hot water over grounds"},
            {"action": "Steep", "description": "Let steep for 4 minutes"},
            {"action": "Press", "description": "Slowly press down the plunger"},
            {"action": "Serve", "description": "Pour and enjoy immediately"}
        ],
        skill_level="beginner",
        success_rate=0.85
    )
    
    # Demonstrate retrieval and search
    print("=== Memory Manager Demo ===")
    print(f"Memory Statistics: {mm.get_memory_stats()}")
    
    # Search episodic memories
    work_memories = mm.search_episodic_memories(tags=["work"])
    print(f"\nWork-related memories found: {len(work_memories)}")
    
    # Search semantic memories by category
    programming_knowledge = mm.search_semantic_memories(category="Programming Languages")
    print(f"Programming language knowledge: {len(programming_knowledge)}")
    
    # Search procedural memories
    beginner_procedures = mm.search_procedural_memories(skill_level="beginner")
    print(f"Beginner-level procedures: {len(beginner_procedures)}")
    
    # Export all memories
    export_file = mm.export_memories("demo_export.json")
    print(f"\nMemories exported to: {export_file}")