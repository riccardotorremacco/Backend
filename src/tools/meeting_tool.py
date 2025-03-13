from langchain.tools import BaseTool
from typing import Literal, Optional, List
from pydantic import BaseModel, Field
from memory_handler import ConversationMemory

# Input schema for meeting-related actions
class MeetingInput(BaseModel):
    action: Literal['schedule', 'list', 'cancel'] = Field(description="Action to perform: 'schedule', 'list', or 'cancel'")
    date: str = Field(description="Meeting date in YYYY-MM-DD format")
    time: Optional[str] = Field(None, description="Meeting time in HH:MM format")
    title: Optional[str] = Field(None, description="Meeting title")
    participants: Optional[List[str]] = Field(None, description="List of participants")

class MeetingTool(BaseTool):
    def __init__(self, memory_handler: ConversationMemory):
        super().__init__(
            name="meeting_tool", 
            description="Manages meeting, scheduling, listing and canceling meetings. Use it to schedule a new meeting, listing all meetings, or canceling one.",
            args_schema=MeetingInput
        )
        self._memory_handler = memory_handler

    def _run(
            self, 
            action: str, 
            date: str, 
            time: Optional[str] = None, 
            title: Optional[str] = None, 
            participants: Optional[List[str]] = None,
            **kwargs
        ) -> str:
        # Aggiungi **kwargs per catturare eventuali parametri aggiuntivi, incluso tool_call_id
        
        print(f"[DEBUG] Calling MeetingTool: action={action}, date={date}, time={time}, title={title}, participants={participants}")
        
        # Perform the specified action

        # Schedule a meeting
        if action == "schedule":
            if not all([time, title, participants]):
                return "Error: Missing required fields for scheduling a meeting. Please provide time, title, and participants."
            
            meeting = {
                "date": date, 
                "time": time, 
                "title": title, 
                "participants": participants
            }
            self._memory_handler.append_memory({"type": "meeting", "data": meeting})
            return f"Scheduled meeting '{title}' on {date} at {time} with {', '.join(participants)}"

        # List meetings for a specific date
        elif action == "list":
            filters = {}
            if date:
                filters["date"] = date

            meetings = self._memory_handler.get_memory("meeting", filters=filters)

            if not meetings:
                return f"No meetings found."
            
            meeting_infos = []
            for m in meetings:
                meeting_title = m["data"]["title"]
                meeting_time = m["data"]["time"]
                meeting_participants = m["data"]["participants"]

                meeting_info = f"- {meeting_title} at {meeting_time} with {', '.join(meeting_participants)}"
                meeting_infos.append(meeting_info)

            meetings = "Found the following meetings:\n" + "\n".join(meeting_infos)
            print(f"[DEBUG] {meetings}")
            return meetings

        elif action == "cancel":
            if not title:
                return "Error: Title is required for cancellation."

            self._memory_handler.delete_memory(
                "meeting", lambda m: m["data"]["date"] == date and m["data"]["title"] == title
            )
            return f"Cancelled meeting '{title}' scheduled for {date}"

        return "Invalid action. Please use 'schedule', 'list', or 'cancel'."
