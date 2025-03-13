import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from fastapi.staticfiles import StaticFiles


# Importa le funzioni necessarie dal main
from main import create_assistants

frontend_build_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build')

# DEBUG: Stampa informazioni sul percorso e contenuto
print(f"Frontend build path: {frontend_build_path}")
print(f"Il percorso esiste: {os.path.exists(frontend_build_path)}")
if os.path.exists(frontend_build_path):
    print(f"Contenuto della directory: {os.listdir(frontend_build_path)}")
    static_path = os.path.join(frontend_build_path, 'static')
    if os.path.exists(static_path):
        print(f"Contenuto della directory static: {os.listdir(static_path)}")
        js_path = os.path.join(static_path, 'js')
        if os.path.exists(js_path):
            print(f"Contenuto della directory js: {os.listdir(js_path)}")

# Inizializza l'app FastAPI
app = FastAPI(
    title="API Assistente Comune di Napoli",
    description="API per l'assistente virtuale del Comune di Napoli",
    version="1.0.0"
)

# Abilita CORS per permettere le richieste dal tuo frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, specifica l'URL esatto del tuo frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DEBUG: Aggiunge una route specifica per verificare l'accesso ai file statici
@app.get("/test-static")
async def test_static():
    return {
        "build_path_exists": os.path.exists(frontend_build_path),
        "index_exists": os.path.exists(os.path.join(frontend_build_path, "index.html")),
        "js_main_exists": os.path.exists(os.path.join(frontend_build_path, "static/js/main.ef0fcb83.js")),
        "css_main_exists": os.path.exists(os.path.join(frontend_build_path, "static/css/main.b7068f00.css"))
    }

# Resto del tuo codice...

# Definisci i modelli di dati
class Message(BaseModel):
    role: str
    content: str

class ConversationRequest(BaseModel):
    messages: List[Message]

class ConversationResponse(BaseModel):
    response: str
    conversation_id: Optional[str] = None

# Inizializza l'assistente
knowledge_file = os.getenv("KNOWLEDGE_BASE_PATH", "knowledge_base.txt")
agent, memory_saver = create_assistants(knowledge_file)

@app.post("/api/chat", response_model=ConversationResponse)
async def chat(request: ConversationRequest = Body(...)):
    # Il resto del tuo codice...
    pass

@app.post("/api/reset")
async def reset_conversation():
    # Il resto del tuo codice...
    pass

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

# IMPORTANTE: Le route API devono essere definite PRIMA del mount dei file statici
# altrimenti le richieste verranno intercettate dal gestore dei file statici

# Monta i file statici
app.mount("/", StaticFiles(directory=frontend_build_path, html=True), name="static")

# Funzione per avviare il server API
def start_api_server(host="0.0.0.0", port=8000):
    """Avvia il server API FastAPI"""
    print(f"\nAvvio del server API su http://{host}:{port}")
    print(f"Per testare i file statici, visita http://{host}:{port}/test-static")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    # Se eseguito direttamente, avvia il server API
    start_api_server()