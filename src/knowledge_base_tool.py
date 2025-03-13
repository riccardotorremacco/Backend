import os
from langchain_core.tools import Tool
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain_aws import ChatBedrock
import boto3
from botocore.config import Config

class KnowledgeBaseTool:
    """Tool per accedere alla base di conoscenza da un file di testo."""
    
    def __init__(self, memory, knowledge_file_path, model=None):
        self.memory = memory
        self.knowledge_file_path = knowledge_file_path
        self.model = model if model is not None else self._get_llm()
        self.vectorstore = self._create_vectorstore()
        
        self.tool = Tool(
            name="knowledge_base",
            description="Cerca informazioni nella base di conoscenza del Comune di Napoli. Usa questo tool quando l'utente chiede informazioni sui servizi comunali.",
            func=self.query_knowledge_base
        )
    
    def _get_llm(self):
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
    
    def _create_vectorstore(self):
        with open(self.knowledge_file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        # Creiamo un array con l'intero testo come singolo documento
        texts = [text]
        
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        
        return FAISS.from_texts(texts, embeddings)
    
    def query_knowledge_base(self, query):
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 1}  # Recupera solo il documento più rilevante
        )
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.model,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )
        
        result = qa_chain.invoke({"query": query})
        
        return result['result']

    def get_tool(self):
        return self.tool