import pickle
import heapq
from typing import List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Task:
    """Represents a single task with priority and execution details."""
    name: str
    function: Callable
    priority: int = 1  # Lower number = higher priority
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __lt__(self, other):
        """Enable heap comparison based on priority."""
        return self.priority < other.priority


class TaskScheduler:
    """Simple task scheduler with priority handling and persistence."""
    
    def __init__(self, persistence_file: str = "tasks.pkl"):
        self.tasks: List[Task] = []
        self.persistence_file = persistence_file
        self.load_tasks()
    
    def add_task(self, name: str, function: Callable, priority: int = 1, 
                 args: tuple = (), kwargs: dict = None) -> None:
        """Add a task to the scheduler."""
        kwargs = kwargs or {}
        task = Task(name, function, priority, args, kwargs)
        heapq.heappush(self.tasks, task)
        self.save_tasks()
        print(f"Added task: {name} (priority: {priority})")
    
    def remove_task(self, name: str) -> bool:
        """Remove a task by name. Returns True if found and removed."""
        for i, task in enumerate(self.tasks):
            if task.name == name:
                del self.tasks[i]
                heapq.heapify(self.tasks)  # Restore heap property
                self.save_tasks()
                print(f"Removed task: {name}")
                return True
        print(f"Task not found: {name}")
        return False
    
    def execute_next(self) -> Optional[Any]:
        """Execute the highest priority task."""
        if not self.tasks:
            print("No tasks to execute")
            return None
        
        task = heapq.heappop(self.tasks)
        self.save_tasks()
        
        try:
            print(f"Executing task: {task.name}")
            result = task.function(*task.args, **task.kwargs)
            print(f"Task completed: {task.name}")
            return result
        except Exception as e:
            print(f"Task failed: {task.name} - {e}")
            return None
    
    def execute_all(self) -> List[Any]:
        """Execute all tasks in priority order."""
        results = []
        while self.tasks:
            result = self.execute_next()
            results.append(result)
        return results
    
    def list_tasks(self) -> None:
        """Display all pending tasks."""
        if not self.tasks:
            print("No pending tasks")
            return
        
        print("Pending tasks (by priority):")
        sorted_tasks = sorted(self.tasks)
        for i, task in enumerate(sorted_tasks, 1):
            print(f"{i}. {task.name} (priority: {task.priority}, "
                  f"created: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')})")
    
    def save_tasks(self) -> None:
        """Save tasks to pickle file."""
        try:
            with open(self.persistence_file, 'wb') as f:
                # Save only serializable task data
                task_data = [(t.name, t.priority, t.args, t.kwargs, t.created_at) 
                           for t in self.tasks]
                pickle.dump(task_data, f)
        except Exception as e:
            print(f"Failed to save tasks: {e}")
    
    def load_tasks(self) -> None:
        """Load tasks from pickle file."""
        try:
            with open(self.persistence_file, 'rb') as f:
                task_data = pickle.load(f)
                # Note: Functions are not restored from pickle
                # Only task metadata is preserved
                print(f"Loaded {len(task_data)} task records from {self.persistence_file}")
        except (FileNotFoundError, EOFError):
            print(f"No existing task file found: {self.persistence_file}")
        except Exception as e:
            print(f"Failed to load tasks: {e}")
    
    def clear_all(self) -> None:
        """Clear all tasks."""
        self.tasks.clear()
        self.save_tasks()
        print("All tasks cleared")


# Example usage and demo functions
def sample_task(message: str = "Hello World!") -> str:
    """Sample task function for demonstration."""
    print(f"Task output: {message}")
    return message


def math_task(a: int, b: int, operation: str = "add") -> int:
    """Sample math task."""
    if operation == "add":
        result = a + b
    elif operation == "multiply":
        result = a * b
    else:
        result = 0
    print(f"Math result: {result}")
    return result


if __name__ == "__main__":
    # Demo usage
    scheduler = TaskScheduler("demo_tasks.pkl")
    
    # Add some sample tasks
    scheduler.add_task("greeting", sample_task, priority=2, 
                      kwargs={"message": "Welcome to TaskScheduler!"})
    scheduler.add_task("urgent_calc", math_task, priority=1, 
                      args=(10, 5), kwargs={"operation": "multiply"})
    scheduler.add_task("simple_calc", math_task, priority=3, args=(2, 3))
    
    # List and execute tasks
    scheduler.list_tasks()
    print("\n" + "="*50)
    scheduler.execute_all()