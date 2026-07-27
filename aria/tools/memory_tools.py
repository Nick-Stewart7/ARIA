from strands import tool
import os
from memory_manager import MemoryManager

@tool
def store(session_id: str, memory: str):
    memory_manager = MemoryManager()
    try:
        memory_manager.store(session_id, memory)
    except Exception as e:
        print(f"Error performing memory store: {e}")

@tool
def recall(query: str, n_results: int):
    memory_manager = MemoryManager()
    try:
        memory_manager.recall(query, n_results)
    except Exception as e:
        print(f"Error performing memory recall: {e}")