#!/usr/bin/env python3
"""
Test script for Memory Manager
===============================

Simple tests to verify the three-tier memory architecture works correctly.
"""

import sys
import os
import tempfile
import shutil
from ARIA.artifacts.code.memory_manager import MemoryManager


def test_episodic_memory():
    """Test episodic memory functionality."""
    print("Testing Episodic Memory...")
    
    # Create temporary directory for testing
    test_dir = tempfile.mkdtemp(prefix="test_memory_")
    mm = MemoryManager(test_dir)
    
    try:
        # Store episodic memory
        memory = mm.store_episodic_memory(
            "test_event",
            "Testing episodic memory storage",
            {"location": "test environment", "participants": ["tester"]},
            emotional_weight=0.5,
            tags=["test", "memory"]
        )
        
        # Verify storage
        assert memory.id == "test_event"
        assert memory.event == "Testing episodic memory storage"
        assert memory.emotional_weight == 0.5
        assert "test" in memory.tags
        
        # Test retrieval
        retrieved = mm.retrieve_episodic_memory("test_event")
        assert retrieved is not None
        assert retrieved.event == memory.event
        
        # Test search
        results = mm.search_episodic_memories(tags=["test"])
        assert len(results) == 1
        assert results[0].id == "test_event"
        
        print("[PASS] Episodic memory tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Episodic memory test failed: {e}")
        return False
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_semantic_memory():
    """Test semantic memory functionality."""
    print("Testing Semantic Memory...")
    
    test_dir = tempfile.mkdtemp(prefix="test_memory_")
    mm = MemoryManager(test_dir)
    
    try:
        # Store semantic memory
        memory = mm.store_semantic_memory(
            "test_concept",
            "Test Concept",
            "A concept used for testing the memory system",
            "Testing",
            {"type": "unit_test", "purpose": "validation"},
            confidence=0.95
        )
        
        # Verify storage
        assert memory.id == "test_concept"
        assert memory.concept == "Test Concept"
        assert memory.category == "Testing"
        assert memory.confidence == 0.95
        
        # Test retrieval
        retrieved = mm.retrieve_semantic_memory("test_concept")
        assert retrieved is not None
        assert retrieved.concept == memory.concept
        
        # Test search
        results = mm.search_semantic_memories(category="Testing")
        assert len(results) == 1
        assert results[0].id == "test_concept"
        
        # Test categories
        categories = mm.get_semantic_categories()
        assert "Testing" in categories
        
        print("[PASS] Semantic memory tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Semantic memory test failed: {e}")
        return False
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_procedural_memory():
    """Test procedural memory functionality."""
    print("Testing Procedural Memory...")
    
    test_dir = tempfile.mkdtemp(prefix="test_memory_")
    mm = MemoryManager(test_dir)
    
    try:
        # Store procedural memory
        steps = [
            {"action": "Step 1", "description": "First step"},
            {"action": "Step 2", "description": "Second step"}
        ]
        
        memory = mm.store_procedural_memory(
            "test_procedure",
            "Test Procedure",
            "A procedure for testing",
            steps,
            skill_level="beginner",
            success_rate=0.8
        )
        
        # Verify storage
        assert memory.id == "test_procedure"
        assert memory.name == "Test Procedure"
        assert memory.skill_level == "beginner"
        assert memory.success_rate == 0.8
        assert len(memory.steps) == 2
        
        # Test retrieval
        retrieved = mm.retrieve_procedural_memory("test_procedure")
        assert retrieved is not None
        assert retrieved.name == memory.name
        
        # Test search
        results = mm.search_procedural_memories(skill_level="beginner")
        assert len(results) == 1
        assert results[0].id == "test_procedure"
        
        # Test success rate update
        mm.update_procedure_success_rate("test_procedure", 0.9)
        updated = mm.retrieve_procedural_memory("test_procedure")
        assert updated.success_rate == 0.9
        
        print("[PASS] Procedural memory tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Procedural memory test failed: {e}")
        return False
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_persistence():
    """Test memory persistence functionality."""
    print("Testing Memory Persistence...")
    
    test_dir = tempfile.mkdtemp(prefix="test_memory_")
    
    try:
        # Create first manager and store memories
        mm1 = MemoryManager(test_dir)
        
        mm1.store_episodic_memory(
            "persist_test",
            "Persistence test event",
            {"test": True}
        )
        
        mm1.store_semantic_memory(
            "persist_concept",
            "Persistence Concept",
            "Testing persistence",
            "Testing"
        )
        
        mm1.store_procedural_memory(
            "persist_procedure",
            "Persistence Procedure",
            "Testing persistence",
            [{"action": "test", "description": "test step"}]
        )
        
        # Create second manager and verify persistence
        mm2 = MemoryManager(test_dir)
        
        # Verify memories persisted
        episodic = mm2.retrieve_episodic_memory("persist_test")
        semantic = mm2.retrieve_semantic_memory("persist_concept")
        procedural = mm2.retrieve_procedural_memory("persist_procedure")
        
        assert episodic is not None
        assert semantic is not None
        assert procedural is not None
        
        stats = mm2.get_memory_stats()
        assert stats["total_memories"] == 3
        
        print("[PASS] Persistence tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Persistence test failed: {e}")
        return False
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_memory_management():
    """Test memory management features."""
    print("Testing Memory Management...")
    
    test_dir = tempfile.mkdtemp(prefix="test_memory_")
    mm = MemoryManager(test_dir)
    
    try:
        # Store some memories
        mm.store_episodic_memory("mgmt_test1", "Event 1", {})
        mm.store_semantic_memory("mgmt_test2", "Concept 1", "Description", "Category")
        mm.store_procedural_memory("mgmt_test3", "Procedure 1", "Description", [])
        
        # Test statistics
        stats = mm.get_memory_stats()
        assert stats["episodic_count"] == 1
        assert stats["semantic_count"] == 1
        assert stats["procedural_count"] == 1
        assert stats["total_memories"] == 3
        
        # Test deletion
        deleted = mm.delete_memory("episodic", "mgmt_test1")
        assert deleted == True
        
        stats = mm.get_memory_stats()
        assert stats["episodic_count"] == 0
        assert stats["total_memories"] == 2
        
        # Test export
        export_file = mm.export_memories(os.path.join(test_dir, "test_export.json"))
        assert os.path.exists(export_file)
        
        print("[PASS] Memory management tests passed")
        return True
        
    except Exception as e:
        print(f"[FAIL] Memory management test failed: {e}")
        return False
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def run_all_tests():
    """Run all tests."""
    print("=" * 50)
    print("MEMORY MANAGER TEST SUITE")
    print("=" * 50)
    
    tests = [
        test_episodic_memory,
        test_semantic_memory,
        test_procedural_memory,
        test_persistence,
        test_memory_management
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    print("=" * 50)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)