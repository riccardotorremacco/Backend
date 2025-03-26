import os
from langchain_core.tools import Tool
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain_aws import ChatBedrock
import boto3
from botocore.config import Config
import textwrap

class KnowledgeBaseTool:
    """Tool per accedere alla base di conoscenza da un file di testo."""
    
    def __init__(self, memory, knowledge_file_path, model=None):
        self.memory = memory
        self.knowledge_file_path = knowledge_file_path
        self.model = model if model is not None else self._get_llm()
        self.vectorstore = self._create_vectorstore()
        
        self.tool = Tool(
            name="knowledge_base",
            description="Cerca informazioni nella base di conoscenza del Comune di Napoli.",
            func=self.query_knowledge_base
        )
    
    def _get_llm(self):
        # Codice per il modello LLM (come nel tuo esempio)
        pass
    
    def _create_vectorstore(self):
        with open(self.knowledge_file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        # Suddividi il testo in chunk (ad esempio, per 500 caratteri)
        chunk_size = 500
        chunks = textwrap.wrap(text, chunk_size)
        
        # Creiamo embeddings per ciascun chunk
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        
        # Costruisci il vectorstore con i chunk
        return FAISS.from_texts(chunks, embeddings)
        
    def query_knowledge_base(self, query):
   

        # print(self.vectorstore.__dict__)
        # Fase 2: Recupero informazioni dalla knowledge base
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}  # Recupera più documenti per dare più contesto
        )
        

        #print(f"\n\n\n\n\nretriever: {retriever.get_relevant_documents("SERVIZI TRIBUTARI")}")
#        docs = retriever.get_relevant_documents(query)
        docs = retriever.invoke(query)

#print("\n\n\n\n\nDocumenti recuperati:", docs)
        return docs



        qa_chain = RetrievalQA.from_chain_type(
            llm=self.model,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )
        
        # Risposta alla query
        result = qa_chain.invoke({"query": query})
        print('KB_Result: ',result['result'])

        return result['result']

    def get_tool(self):
        return self.tool
