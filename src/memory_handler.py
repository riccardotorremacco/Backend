
import os
import json
from typing import Dict, Any, Optional, Callable
from langgraph.checkpoint.memory import MemorySaver

class ConversationMemory(MemorySaver):
    """Memory handler per memorizzare e recuperare dati delle conversazioni."""

    def __init__(self, file_path: str = "data/conversation_memory.json"):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        self.file_path = file_path
        self._load_memory()    

    def _load_memory(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                self.memory = json.load(f)
        else:
            self.memory = {"messages": [], "entries": []}  
            self.save(self.memory)

    def save(self, state: Dict[str, Any]):
        """Salva lo stato attuale in memoria"""
        self.memory = state
        with open(self.file_path, 'w') as f:
            json.dump(state, f, indent=2)

    def load(self) -> Dict[str, Any]:
        """Carica lo stato della memoria"""
        return self.memory

    def append_memory(self, entry: Dict):
        """Aggiunge un nuovo elemento alla memoria."""
        if "entries" not in self.memory:
            self.memory["entries"] = []
        self.memory["entries"].append(entry)
        self.save(self.memory)

    def get_memory(self, entry_type: str, filters: Optional[Dict] = None) -> list:
        """Recupera elementi di un tipo specifico con filtri opzionali."""
        results = [entry for entry in self.memory.get("entries", []) if entry.get("type") == entry_type]
        if filters:
            for key, value in filters.items():
                results = [entry for entry in results if entry["data"].get(key) == value]
        return results

    def delete_memory(self, entry_type: str, condition: Callable[[Dict], bool]):
        """Elimina elementi di un tipo specifico in base a una condizione."""
        self.memory["entries"] = [
            entry for entry in self.memory.get("entries", [])
            if entry.get("type") != entry_type or not condition(entry)
        ]
        self.save(self.memory)

    def reset_messages(self):
        """Resetta i messaggi della conversazione."""
        self.memory["messages"] = []
        self.save(self.memory)
