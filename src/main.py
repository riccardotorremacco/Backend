import os
from dotenv import load_dotenv
from datetime import datetime
import boto3
from botocore.config import Config
import urllib3
import sys

from langchain_aws import ChatBedrock
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.prebuilt import create_react_agent

from memory_handler import ConversationMemory
from knowledge_base_tool import KnowledgeBaseTool

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
import uvicorn

import glob
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
from save_report_tool import SaveReportTool  # Importa il nuovo tool

#logging.basicConfig(level=logging.INFO)
#logger = logging.getLogger(__name__)

#logger.info("Messaggio di debug-main")


load_dotenv()



##################################################################################################


# Inizializza l'app FastAPI
app = FastAPI(
    title="API Assistente Comune di Napoli",
    description="API per l'assistente virtuale del Comune di Napoli",
    version="1.0.0"
)


# Abilita CORS (in produzione, specifica l'URL esatto del frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Definisci una rotta di esempio
@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


# Modelli di dati
class Message(BaseModel):
    role: str
    content: str

class ConversationRequest(BaseModel):
    messages: List[Message]

class ConversationResponse(BaseModel):
    response: str
    conversation_id: Optional[str] = None


# Avvia il server API
def start_api_server(host="0.0.0.0", port=8000):
    
    uvicorn.run(app, host=host, port=port)
    logger.info(f"\nAvvio del server API su http://{host}:{port}")
    logger.info(f"Per testare i file statici, visita http://{host}:{port}/test-static")



#############################################################################################################


def get_llm():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    bedrock_client = boto3.client(
        service_name='bedrock-runtime',
        region_name='eu-west-1',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        verify=False,
        config=Config(proxies={'https': None})
    )

    model = ChatBedrock(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        client=bedrock_client,
        model_kwargs={
            "temperature": 0,
            "max_tokens": 2000,
        }
    )

    return model

def create_assistants(knowledge_file_path="knowledge_base.txt"):
    """Inizializza l'agente e gli strumenti"""
    
    model = get_llm()
    current_date = datetime.now().strftime("%B %d, %Y")
    memory = ConversationMemory()
    kb_tool = KnowledgeBaseTool(memory, knowledge_file_path, model)

    # Verifica se la directory per i report esiste, altrimenti la crea
    report_dir = "data"
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)


    report_tool = SaveReportTool(memory, report_file_path="segnalazioni.txt")  # Nuovo tool per segnalazioni

    agent_prompt = f"""Sei un assistente virtuale del Comune di Napoli. La tua funzione è fornire informazioni sui servizi comunali basandoti esclusivamente sulla knowledge base a tua disposizione.
### Linee guida di comportamento:  
- se l'utente ti saluta limitati a salutarlo a tua volta.
-  **Usa SOLO le informazioni presenti nella knowledge base.** Se non trovi una risposta, dichiara che non hai informazioni su quell’argomento e indica gli ambiti in cui puoi aiutare.  
- **Non inventare informazioni, non fornire risposte generiche e non speculare su temi non presenti nella knowledge base.**  
- Se l'utente chiede "Di cosa puoi parlarmi?" o domande simili, elenca SOLO gli argomenti di cui disponi di informazioni, senza aggiungere dettagli non verificabili.  
- Se l'utente chiede qualcosa di non presente nella knowledge base, rispondi con: "Mi dispiace, non dispongo di informazioni su questo argomento. Posso aiutarti con [elenco degli ambiti disponibili]?"  

Regole linguistiche:
- Se l'utente parla in inglese, rispondi in inglese. Se l'utente parla in italiano, rispondi in italiano. Non mischiare le lingue.
-- **Rispondi nella stessa lingua dell'utente**, senza mescolare le lingue.  

Gestione delle segnalazioni:
Se l'utente segnala un problema:
1. Se il messaggio contiene sia il luogo che la descrizione del problema, salva la segnalazione con il tool save_report_tool, ringrazia l'utente e conferma che la segnalazione è stata registrata.
2. Se manca il luogo o la descrizione, chiedi all'utente di fornire entrambi i dettagli prima di registrare la segnalazione.
3. Se il messaggio sembra riferirsi a un problema negativo per i cittadini, richiama save_report_tool e memorizza la segnalazione.

Ora attendi l'input dell'utente e segui queste linee guida per rispondere.
"""


    agent = create_react_agent(
        model=model,
        tools=[kb_tool.get_tool(),report_tool.get_tool()],
        
        state_modifier=agent_prompt,
    )

    return agent, memory


knowledge_file = os.getenv("KNOWLEDGE_BASE_PATH", "knowledge_base.txt")

agent, memory_saver = create_assistants(knowledge_file)



def main():
    start_api_server()
    logger.info("\nBenvenuto nell'Assistente del Comune di Napoli!")
    
    if len(sys.argv) > 1:
        knowledge_file = sys.argv[1]
    
    if not os.path.exists(knowledge_file):
        print(f"Attenzione: Il file {knowledge_file} non esiste. Verrà creato un file vuoto.")
        with open(knowledge_file, 'w', encoding='utf-8') as f:
            f.write("Base di conoscenza del Comune di Napoli")

    
    while True:
        state = memory_saver.load()
        
        user_input = input("\nUser: ")
        
        if user_input.lower() in ['quit', 'exit', '/quit', '/exit']:
            print("\nArrivederci!")
            memory_saver.reset_messages()
            break
        
        messages = state.get("messages", [])
        messages.append({"role": "user", "content": user_input})
        
        inputs = {
            "messages": messages
        }
        
        for event in agent.stream(inputs, stream_mode="values"):
            logger.info("Event:", event)  # <-- Logga tutto per debugging
            if "messages" in event:
                message = event["messages"][-1]
                
                if isinstance(message, AIMessage):
                    logger.info("AI Response: ",message.content)
                if isinstance(message, ToolMessage):
                    logger.info("Tool Response: ",message.content)


#__________________________________________________________________









#____________________________________________________________________


@app.post("/api/chat", response_model=ConversationResponse)
async def chat(request: ConversationRequest = Body(...)):
    state = memory_saver.load()
    # Verifica che il primo messaggio abbia il ruolo "user"
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    
    if messages and messages[0]["role"] != "user":
        # Aggiungi un messaggio di tipo "user" se il primo messaggio non è di tipo "user"
        messages.insert(0, {"role": "user", "content": "User starts the conversation."})

    state["messages"] = messages

    inputs = {"messages": messages}
    response_text = ""

    for event in agent.stream(inputs, stream_mode="values"):
        if "messages" in event:
            message = event["messages"][-1]
            if isinstance(message, AIMessage):
                response_text = message.content
    
    return ConversationResponse(response=response_text)



@app.post("/api/reset")
async def reset_conversation():
    memory_saver.reset()
    return {"status": "conversation reset"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}





if __name__ == "__main__":
    main()



