from langchain.tools import BaseTool
from typing import Literal, Optional
from pydantic import BaseModel, Field
from memory_handler import ConversationMemory

# Input schema for documentation-related actions
class TodoInput(BaseModel):
    action: Literal['add', 'list', 'delete'] = Field(description="Action to perform: 'add', 'list', or 'delete'")
    task: Optional[str] = Field(None, description="Task description")
    priority: Optional[str] = Field(None, description="Priority level: high, medium, or low")
    due_date: Optional[str] = Field(None, description="Due date in YYYY-MM-DD format")
    status: Optional[str] = Field(None, description="Status of the task")

class TodoTool(BaseTool):
    def __init__(self, memory_handler: ConversationMemory):
        super().__init__(
            name="todo_tool", 
            description="manage task and todos like add, list, complete and delete. Use this tool to add a new task, list all tasks that are in, complete a task, or delete a task.",
            args_schema=TodoInput
        )
        self._memory_handler = memory_handler

    # Core function for processing actions based on agent input
    def _run(self, action: str, task: Optional[str] = None, 
             priority: Optional[str] = None, due_date: Optional[str] = None, 
             status: Optional[str] = None, **kwargs) -> str:
        # Aggiungi **kwargs per catturare eventuali parametri aggiuntivi, incluso tool_call_id
        
        print(f"\n[DEBUG] TodoTool received: action={action}, task={task}, priority={priority}, due_date={due_date}, status={status}")
        print(f"[DEBUG] Additional kwargs: {kwargs}")  # Utile per debug

        # Perform the specified action
        if action == "add":
            if not task:
                return "Error: Task description is required."

            todo = {"task": task, "priority": priority, "due_date": due_date, "status": status if status else "pending"}
            self._memory_handler.append_memory({"type": "todo", "data": todo})
            return f"Added task: '{task}'" + (f" with priority {priority}" if priority else "") + \
                (f" and due date {due_date}" if due_date else "")

        elif action == "list":
            todos = self._memory_handler.get_memory("todo")
            if not todos:
                return "No tasks found."

            return "Tasks:\n" + "\n".join(
                [f"- {t['data']['task']} (Priority: {t['data'].get('priority', 'N/A')}, Due: {t['data'].get('due_date', 'N/A')}, Status: {t['data'].get('status', 'unknown')})"
                for t in todos]
            )

        elif action == "delete":
            if not task:
                return "Error: Task description is required for deletion."

            self._memory_handler.delete_memory("todo", lambda t: t["data"]["task"] == task)
            return f"Deleted task: '{task}'"

        return "Invalid action. Please use 'add', 'list', 'complete', or 'delete' for task/todo."