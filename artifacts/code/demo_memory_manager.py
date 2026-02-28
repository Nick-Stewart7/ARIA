#!/usr/bin/env python3
"""
Memory Manager Demonstration
============================

This script demonstrates the three-tier memory architecture implementation
with practical examples of storing and retrieving different types of memories.
"""

from ARIA.artifacts.code.memory_manager import MemoryManager, EpisodicMemory, SemanticMemory, ProceduralMemory
import json
from datetime import datetime, timedelta


def demonstrate_episodic_memory(mm: MemoryManager):
    """Demonstrate episodic memory functionality."""
    print("=" * 50)
    print("EPISODIC MEMORY DEMONSTRATION")
    print("=" * 50)
    
    # Store various episodic memories
    memories_to_store = [
        {
            "id": "birthday_party_2024",
            "event": "Sarah's 30th birthday party",
            "context": {
                "location": "Downtown restaurant",
                "guests": ["Mike", "Lisa", "Tom", "Anna"],
                "activities": ["dinner", "cake", "dancing"],
                "gift_given": "Photo album"
            },
            "emotional_weight": 0.8,
            "tags": ["birthday", "celebration", "friends", "social"]
        },
        {
            "id": "first_python_bug",
            "event": "Spent 3 hours debugging a missing comma",
            "context": {
                "location": "Home office",
                "project": "Web scraper",
                "error_type": "SyntaxError",
                "lesson_learned": "Always check punctuation first"
            },
            "emotional_weight": -0.3,
            "tags": ["programming", "debugging", "learning", "frustration"]
        },
        {
            "id": "graduation_ceremony",
            "event": "Computer Science degree graduation",
            "context": {
                "university": "Tech University",
                "degree": "BS Computer Science",
                "gpa": 3.7,
                "family_present": ["Mom", "Dad", "Sister"]
            },
            "emotional_weight": 0.9,
            "tags": ["achievement", "education", "family", "milestone"]
        }
    ]
    
    # Store the memories
    for mem_data in memories_to_store:
        memory = mm.store_episodic_memory(**mem_data)
        print(f"[+] Stored episodic memory: {memory.event}")
    
    print(f"\nTotal episodic memories stored: {len(mm.episodic_memories)}")
    
    # Demonstrate search functionality
    print("\n--- Search Examples ---")
    
    # Search by tags
    programming_memories = mm.search_episodic_memories(tags=["programming"])
    print(f"Programming-related memories: {len(programming_memories)}")
    for mem in programming_memories:
        print(f"  - {mem.event} (emotional weight: {mem.emotional_weight})")
    
    # Search by text
    celebration_memories = mm.search_episodic_memories(query="birthday")
    print(f"\nCelebration memories: {len(celebration_memories)}")
    for mem in celebration_memories:
        print(f"  - {mem.event} (tags: {', '.join(mem.tags)})")
    
    # Retrieve specific memory
    specific_memory = mm.retrieve_episodic_memory("first_python_bug")
    if specific_memory:
        print(f"\nSpecific memory details:")
        print(f"  Event: {specific_memory.event}")
        print(f"  Context: {specific_memory.context}")
        print(f"  Emotional impact: {specific_memory.emotional_weight}")


def demonstrate_semantic_memory(mm: MemoryManager):
    """Demonstrate semantic memory functionality."""
    print("\n" + "=" * 50)
    print("SEMANTIC MEMORY DEMONSTRATION")
    print("=" * 50)
    
    # Store semantic memories (general knowledge)
    knowledge_base = [
        {
            "id": "machine_learning_basics",
            "concept": "Machine Learning",
            "description": "A subset of AI that enables systems to learn from data without explicit programming",
            "category": "Computer Science",
            "attributes": {
                "types": ["supervised", "unsupervised", "reinforcement"],
                "key_algorithms": ["neural networks", "decision trees", "SVM"],
                "applications": ["image recognition", "NLP", "recommendation systems"]
            },
            "confidence": 0.9,
            "related_concepts": ["artificial_intelligence", "data_science", "statistics"]
        },
        {
            "id": "coffee_knowledge",
            "concept": "Coffee Bean Types",
            "description": "Main varieties of coffee beans and their characteristics",
            "category": "Food & Beverage",
            "attributes": {
                "arabica": "Smooth, sweet flavor, higher acidity",
                "robusta": "Stronger, more bitter, higher caffeine",
                "origin_regions": ["South America", "Africa", "Asia"]
            },
            "confidence": 0.75,
            "related_concepts": ["brewing_methods", "coffee_culture"]
        },
        {
            "id": "photosynthesis",
            "concept": "Photosynthesis Process",
            "description": "Process by which plants convert sunlight into chemical energy",
            "category": "Biology",
            "attributes": {
                "equation": "6CO2 + 6H2O + light -> C6H12O6 + 6O2",
                "location": "Chloroplasts",
                "phases": ["light-dependent reactions", "Calvin cycle"]
            },
            "confidence": 0.85,
            "related_concepts": ["cellular_respiration", "ecology", "plant_biology"]
        }
    ]
    
    # Store the semantic memories
    for knowledge in knowledge_base:
        memory = mm.store_semantic_memory(**knowledge)
        print(f"[+] Stored semantic memory: {memory.concept}")
    
    print(f"\nTotal semantic memories stored: {len(mm.semantic_memories)}")
    
    # Demonstrate search and categorization
    print("\n--- Knowledge Search Examples ---")
    
    # Search by category
    cs_knowledge = mm.search_semantic_memories(category="Computer Science")
    print(f"Computer Science knowledge: {len(cs_knowledge)}")
    for mem in cs_knowledge:
        print(f"  - {mem.concept} (confidence: {mem.confidence})")
    
    # Search by text
    science_concepts = mm.search_semantic_memories(query="process")
    print(f"\nConcepts involving processes: {len(science_concepts)}")
    for mem in science_concepts:
        print(f"  - {mem.concept} in {mem.category}")
    
    # Show all categories
    categories = mm.get_semantic_categories()
    print(f"\nKnowledge categories: {', '.join(categories)}")
    
    # High confidence knowledge
    high_conf_knowledge = mm.search_semantic_memories(min_confidence=0.8)
    print(f"\nHigh confidence knowledge (>80%): {len(high_conf_knowledge)}")
    for mem in high_conf_knowledge:
        print(f"  - {mem.concept}: {mem.confidence * 100:.0f}% confidence")


def demonstrate_procedural_memory(mm: MemoryManager):
    """Demonstrate procedural memory functionality."""
    print("\n" + "=" * 50)
    print("PROCEDURAL MEMORY DEMONSTRATION")
    print("=" * 50)
    
    # Store procedural memories (how-to knowledge)
    procedures = [
        {
            "id": "git_workflow",
            "name": "Basic Git Workflow",
            "description": "Standard process for version control with Git",
            "steps": [
                {"action": "git status", "description": "Check current repository status"},
                {"action": "git add .", "description": "Stage all changes"},
                {"action": "git commit -m 'message'", "description": "Commit changes with descriptive message"},
                {"action": "git push origin main", "description": "Push changes to remote repository"},
                {"action": "git pull origin main", "description": "Pull latest changes before starting new work"}
            ],
            "skill_level": "beginner",
            "prerequisites": ["git_installation", "repository_setup"],
            "success_rate": 0.95
        },
        {
            "id": "debug_python_code",
            "name": "Python Debugging Process",
            "description": "Systematic approach to debugging Python applications",
            "steps": [
                {"action": "Read error message", "description": "Carefully examine the traceback"},
                {"action": "Identify error location", "description": "Find the exact line causing the issue"},
                {"action": "Check syntax", "description": "Look for typos, missing brackets, indentation"},
                {"action": "Add print statements", "description": "Insert debug prints to trace execution"},
                {"action": "Use debugger", "description": "Step through code with pdb or IDE debugger"},
                {"action": "Test fix", "description": "Verify the solution works correctly"}
            ],
            "skill_level": "intermediate",
            "prerequisites": ["python_basics", "error_understanding"],
            "success_rate": 0.78
        },
        {
            "id": "make_pasta",
            "name": "Cooking Perfect Pasta",
            "description": "How to cook pasta al dente",
            "steps": [
                {"action": "Boil water", "description": "Fill large pot with water, add salt, bring to boil"},
                {"action": "Add pasta", "description": "Add pasta to boiling water, stir immediately"},
                {"action": "Cook time", "description": "Cook for package time minus 1 minute"},
                {"action": "Test doneness", "description": "Taste test - should be firm but not hard"},
                {"action": "Drain", "description": "Drain immediately, reserve some pasta water"},
                {"action": "Serve", "description": "Mix with sauce and serve immediately"}
            ],
            "skill_level": "beginner",
            "success_rate": 0.88
        }
    ]
    
    # Store the procedural memories
    for procedure in procedures:
        memory = mm.store_procedural_memory(**procedure)
        print(f"[+] Stored procedure: {memory.name}")
    
    print(f"\nTotal procedures stored: {len(mm.procedural_memories)}")
    
    # Demonstrate search functionality
    print("\n--- Procedure Search Examples ---")
    
    # Search by skill level
    beginner_procedures = mm.search_procedural_memories(skill_level="beginner")
    print(f"Beginner-level procedures: {len(beginner_procedures)}")
    for mem in beginner_procedures:
        print(f"  - {mem.name} (success rate: {mem.success_rate * 100:.0f}%)")
    
    # Search by success rate
    reliable_procedures = mm.search_procedural_memories(min_success_rate=0.8)
    print(f"\nReliable procedures (>80% success): {len(reliable_procedures)}")
    for mem in reliable_procedures:
        print(f"  - {mem.name}: {mem.success_rate * 100:.0f}% success rate")
    
    # Show detailed procedure
    git_procedure = mm.retrieve_procedural_memory("git_workflow")
    if git_procedure:
        print(f"\nDetailed procedure: {git_procedure.name}")
        print(f"Description: {git_procedure.description}")
        print("Steps:")
        for i, step in enumerate(git_procedure.steps, 1):
            print(f"  {i}. {step['action']}: {step['description']}")
    
    # Update success rate (simulate learning)
    print("\n--- Simulating Learning ---")
    original_rate = mm.procedural_memories["debug_python_code"].success_rate
    mm.update_procedure_success_rate("debug_python_code", 0.85)
    new_rate = mm.procedural_memories["debug_python_code"].success_rate
    print(f"Updated debugging success rate: {original_rate * 100:.0f}% -> {new_rate * 100:.0f}%")


def demonstrate_memory_management(mm: MemoryManager):
    """Demonstrate memory management features."""
    print("\n" + "=" * 50)
    print("MEMORY MANAGEMENT DEMONSTRATION")
    print("=" * 50)
    
    # Show statistics
    stats = mm.get_memory_stats()
    print("Memory Statistics:")
    for key, value in stats.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    # Export memories
    export_file = mm.export_memories("demo_memories_export.json")
    print(f"\nMemories exported to: {export_file}")
    
    # Demonstrate memory deletion
    print("\n--- Memory Deletion Demo ---")
    print("Deleting a semantic memory...")
    deleted = mm.delete_memory("semantic", "coffee_knowledge")
    if deleted:
        print("[+] Coffee knowledge memory deleted successfully")
        new_stats = mm.get_memory_stats()
        print(f"New semantic memory count: {new_stats['semantic_count']}")
    
    # Show persistence (memories are automatically saved)
    print("\n--- Persistence Demo ---")
    print("Creating new Memory Manager instance to test persistence...")
    mm2 = MemoryManager("demo_memory")
    stats2 = mm2.get_memory_stats()
    print(f"Loaded memories from storage: {stats2['total_memories']} total memories")
    
    print("\n--- Cross-Memory Search Demo ---")
    # Search across all memory types for Python-related content
    python_episodic = mm2.search_episodic_memories(query="python")
    python_semantic = mm2.search_semantic_memories(query="python")
    python_procedural = mm2.search_procedural_memories(query="python")
    
    print("Python-related content across all memory types:")
    print(f"  Episodic memories: {len(python_episodic)}")
    print(f"  Semantic memories: {len(python_semantic)}")  
    print(f"  Procedural memories: {len(python_procedural)}")


def main():
    """Main demonstration function."""
    print("MEMORY MANAGER DEMONSTRATION")
    print("Three-Tier Memory Architecture Implementation")
    print("=" * 60)
    
    # Initialize memory manager with demo storage
    mm = MemoryManager("demo_memory")
    
    # Clear any existing memories for clean demo
    mm.clear_all_memories()
    
    # Demonstrate each memory type
    demonstrate_episodic_memory(mm)
    demonstrate_semantic_memory(mm)
    demonstrate_procedural_memory(mm)
    demonstrate_memory_management(mm)
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE!")
    print("Check the 'demo_memory' directory for persisted memory files.")
    print("=" * 60)


if __name__ == "__main__":
    main()