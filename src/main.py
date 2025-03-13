import os
from dotenv import load_dotenv
from datetime import datetime
import boto3
from botocore.config import Config
import urllib3
import sys
import argparse
from langchain_aws import ChatBedrock
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.prebuilt import create_react_agent

from memory_handler import ConversationMemory
from knowledge_base_tool import KnowledgeBaseTool

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
    
    # Verifica che il file della base di conoscenza esista
    if not os.path.exists(knowledge_file_path):
        print(f"Attenzione: Il file {knowledge_file_path} non esiste. Verrà creato un file vuoto.")
        with open(knowledge_file_path, 'w', encoding='utf-8') as f:
            f.write("Base di conoscenza del Comune di Napoli")
    
    kb_tool = KnowledgeBaseTool(memory, knowledge_file_path, model)

    agent_prompt = f"""
        Sei un assistente virtuale del Comune di Napoli, creato per fornire informazioni sui servizi della pubblica amministrazione.
        La data di oggi è {current_date}

        Segui queste linee guida:
        - Rispondi in modo chiaro, preciso e cordiale alle domande sui servizi comunali
        - Utilizza sempre la cronologia della conversazione per mantenere il contesto
        - Quando l'utente chiede informazioni sui servizi comunali, usa sempre lo strumento knowledge_base per cercare nella base di conoscenza
        - Fornisci informazioni accurate basate sui dati ufficiali del Comune di Napoli dalla base di conoscenza
        - Se non trovi la risposta nella base di conoscenza, indirizza l'utente al sito ufficiale o agli uffici competenti
        - Rispondi in italiano, utilizzando un linguaggio semplice e comprensibile
        - Se la richiesta è ambigua, chiedi gentilmente ulteriori chiarimenti

        Puoi fornire informazioni su:
        - Servizi anagrafici (carta d'identità, certificati, cambio residenza)
        - Sedi degli uffici
        - Qualsiasi altra informazione presente nella base di conoscenza
        
        Non inventare mai informazioni. Se non sei sicuro, indica sempre che l'informazione potrebbe non essere aggiornata
        e suggerisci di verificare sul sito ufficiale del Comune o presso gli uffici competenti.
    """

    agent = create_react_agent(
        model=model,
        tools=[kb_tool.get_tool()],
        state_modifier=agent_prompt,
    )

    return agent, memory

def start_cli_mode(agent, memory_saver):
    """Avvia l'assistente in modalità riga di comando"""
    print("\nBenvenuto nell'Assistente del Comune di Napoli!")
    print("Digita 'exit' o 'quit' per terminare.")
    
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
            if "messages" in event:
                message = event["messages"][-1]
                
                if isinstance(message, AIMessage):
                    print(message.content)

def main():
    # Carica le variabili d'ambiente
    load_dotenv()
    
    # Configura il parser degli argomenti
    parser = argparse.ArgumentParser(description="Assistente Virtuale del Comune di Napoli")
    parser.add_argument("--api", action="store_true", help="Avvia in modalità API server")
    parser.add_argument("--port", type=int, default=8000, help="Porta per il server API (default: 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host per il server API (default: 0.0.0.0)")
    parser.add_argument("--kb", type=str, help="Percorso del file della base di conoscenza")
    
    args = parser.parse_args()
    
    # Imposta il file della base di conoscenza
    knowledge_file = args.kb or os.getenv("KNOWLEDGE_BASE_PATH", "knowledge_base.txt")
    
    # Crea l'assistente
    agent, memory_saver = create_assistants(knowledge_file)
    
    # Avvia nella modalità richiesta
    if args.api:
        # Importa il modulo API solo se necessario
        try:
            from api import start_api_server
            start_api_server(host=args.host, port=args.port)
        except ImportError:
            print("Errore: Modulo API non trovato. Installa fastapi e uvicorn con:")
            print("pip install fastapi uvicorn")
    else:
        # Modalità CLI (default)
        start_cli_mode(agent, memory_saver)

if __name__ == "__main__":
    main()