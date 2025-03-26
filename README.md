# AI Assistant Boilerplate

A scalable Python-based GenAI agent assistant

### Setup
prerequisite: installed Python 3.10.12

1. create a virtual environment:
```bash
python3 -m venv venv
```
2. activate the virtual environment
```bash
# on windows
Set-ExecutionPolicy Unrestricted -Scope Process
.venv\Scripts\activate
# on linux
source venv/bin/activate
```
3. install the requirements  
```bash 
pip install -r requirements.txt
```
4. Add required env variables to '.env'

5. Run the assistant
```bash
python src/main.py
```
## Architecture Overview

The system consists of three main layers:

1. **Control Layer** 
   - Routes requests to appropriate specialized tool
   - Maintains conversation context
   - communicate with user

2. **Tool Layer**
   - **Meeting Tool**: Meeting operations
   - **Todo Tool**: Task management
   - **Documentation Tool**: Note creation/retrieval

### Architecture Diagram

```
┌────────────────────────┐
│         User           │
└───────────┬────────────┘
            │         
       ┌────▼──────┐ 
       │Organizer  │ 
       │Agent      │─┐         
       └─────┬─────┘ │                 
      ┌──────▼───┐   │ 
      │Meeting,  │   │
      │Todo Tools│   │
      └──────────┘   │
             │       │    
             │       │
    ┌────────▼───────▼──────┐
    │  Conversation memory  │
    └──────────────────────-┘
```

## Components Detail

### Organizer Tool
  - Meeting Tool: Schedule/list/cancel meetings
### Todo Tool  
  - Todo Tool: add/list/delete tasks or todos

### Memory handler
- Provide a json file to keep the conversation history for persistent sessions

### Example Usage
# Meeting manager
   ```
   Schedule a team meeting tomorrow at 2 PM with John and Sarah
   Schedule a project review on 2025-05-20 at 10:00 with the development team
   Set up a client call next Monday at 3:30 PM with Microsoft team
   Show me all meetings for 2025-05-20
   Delete my meeting with Microsoft team on next Monday
   ```

# Todo manager
   ```
   Add a high priority task: Review Q4 report, due next Friday
   Show high priority todos
   Complete the task 'Review Q4 report'
   ```

# Combined Examples
   ```
   Schedule a meeting for next Tuesday at 3 PM with Bob for project review and add a todo to prepare slides before this meeting. 
   ```

