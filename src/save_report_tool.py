import os
from langchain_core.tools import Tool
from datetime import datetime

class SaveReportTool:
    """Tool per salvare i messaggi dell'utente in un file quando si tratta di una segnalazione."""

    def __init__(self, memory, report_file_path, model=None):
        self.memory = memory
        self.report_file_path = report_file_path
        self.model = model if model is not None else self._get_llm()  # Carica modello se necessario
        
        # Definisce lo strumento per salvare la segnalazione
        self.tool = Tool(
            name="save_report",
            description="Salva i messaggi di segnalazione in un file di log.",
            func=self.save_report_message
        )
    
    def _get_llm(self):
        """Aggiungi qui il codice per ottenere il modello LLM se necessario."""
        return None
    
    def is_report_message(self, message):
        """Determina se il messaggio è una segnalazione basandosi su parole chiave e luoghi.""" 
        keywords = ["segnala", "errore", "problema", "bug", "questione", "strada rotta", "incidente", "danneggiato", "scippo", "furto", "rapina", "aggressione"]
        locations = ["via", "piazza", "corso", "viale", "vicolo", "strada", "lungomare", "parco", "rotonda"]
        
        # Verifica che il messaggio contenga parole chiave e un luogo
        if any(keyword in message.lower() for keyword in keywords) or any(loc in message.lower() for loc in locations):
            print(f"DEBUG: Messaggio riconosciuto come segnalazione -> {message}")  # Debug
            return True
        
        print(f"DEBUG: Messaggio ignorato -> {message}")  # Debug
        return False
    
    def save_report_message(self, message):
        """Salva il messaggio di segnalazione in un file di log."""
        print(f"DEBUG: save_report_message chiamato con: {message}")  # Debug

        if self.is_report_message(message):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            detailed_message = f"[{timestamp}] {message}"
            self._log_message(detailed_message)  # Salva il messaggio nel file
            
            return f"Grazie per la tua segnalazione. Ho registrato il problema riguardante: {message}. Sarà inoltrato alle autorità competenti."
        else:
            return "Questo non sembra essere un messaggio di segnalazione completo. Ti invito a fornire più dettagli."
    
    def _log_message(self, message):
        """Scrive il messaggio nel file di log."""
        print(f"DEBUG: scrivendo nel file {self.report_file_path}")  # Debug
        try:
            with open(self.report_file_path, 'a', encoding='utf-8') as file:
                file.write(message + "\n")
            print(f"DEBUG: Messaggio salvato correttamente.")  # Debug
        except Exception as e:
            print(f"ERRORE: impossibile scrivere nel file {self.report_file_path} -> {e}")  # Debug
    
    def get_tool(self):
        """Restituisce lo strumento per il salvataggio delle segnalazioni."""
        return self.tool
