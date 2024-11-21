# importing os module for environment variables
import os
# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 

load_dotenv() # Load environment variables from .env file

from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory
from langchain_openai import ChatOpenAI # (Can swap with Gemini AI)

from langchain_community.document_loaders import PyPDFLoader

# from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain_openai import OpenAIEmbeddings # (Can swap with Google Text Embedding)
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import ConfigurableFieldSpec
import database_module

from langchain_chroma import Chroma
from uuid import uuid4
# from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import format_document
from langchain.chains.combine_documents.base import (
    DEFAULT_DOCUMENT_PROMPT,
    DEFAULT_DOCUMENT_SEPARATOR,
)

import logging
# from datetime import datetime
import intent_classifier
import analysis_module
import rollcall_module
import general_module
import teach_module
import guidance_module

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

MONGO_URI = os.environ.get('MONGO_URI')
database_name = 'telegram_bot_db'
chat_collection_name = 'chat_history'

class LLM:
    def __init__(self, model_name: str = None, safety_settings: dict = None, api_key: str = None, text_embedding: str = None, database = None):

        if model_name == None:
            self.model_name = "gemini-1.5-flash"

        if safety_settings == None:
            self.safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
                }
            
        if api_key == None:
            self.api_key = os.environ.get('GOOGLE_API_KEY')

        if text_embedding == None:
            self.text_embedding = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

        if database == None:
            self.database = database_module.DB()
            
        
        # self.llm = ChatGoogleGenerativeAI(model=self.model_name, 
        #                                   safety_settings=self.safety_settings,
        #                                   google_api_key=self.api_key)

        self.llm = ChatOpenAI(model="gpt-4o-mini", api_key= os.environ.get('OPENAI_API_KEY'))

        self.vector_store = Chroma(
                                collection_name="global_doc_collection",
                                embedding_function=self.text_embedding,
                                persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
                            )
        self.retriever = self.vector_store.as_retriever()
        
        self.intent = intent_classifier.Intent_Classifier(self.llm)
        self.analyse = analysis_module.Analyser(self.llm)
        self.rollcall = rollcall_module.Rollcall(self.llm)
        self.general = general_module.General(llm=self.llm, retriever=self.retriever, database=self.database)
        self.teach = teach_module.Teacher(llm=self.llm, retriever=self.retriever, database=self.database)
        self.guide = guidance_module.Guide(llm=self.llm, retriever=self.retriever, database=self.database)

        
        # self.vector_store = InMemoryVectorStore(GoogleGenerativeAIEmbeddings(model=self.text_embedding))
        # self.vector_store = InMemoryVectorStore(embedding=OpenAIEmbeddings())

    # Response to analysis request
    async def analyse_message(self, nusnet_id : str):

        messages = self.database.get_all_conversation(nusnet_id=nusnet_id)
        name = self.database.get_name(nusnet_id=nusnet_id)

        response = await self.analyse.get_analysis(name=name, nusnet_id=nusnet_id, messages=messages)
        
        logging.info(f"Analysis report: {response}")
        
        return response
    
    # Response to rollcall request
    async def rollcall_message(self, nusnet_id : str):

        messages = self.database.get_all_conversation(nusnet_id=nusnet_id)
        name = self.database.get_name(nusnet_id=nusnet_id)

        response = await self.rollcall.get_rollcall(name=name, nusnet_id=nusnet_id, messages=messages)
        
        logging.info(f"Rollcall report: {response}")
        
        return response




    # Response to text message    
    async def response_message(self, message: str, nusnet_id : str, conversation_id: str):

        intention = await self.intent.get_intent(message=message)

        logging.info(f"Intent report: {intention}")

        vector_store = Chroma(
                                collection_name=nusnet_id,
                                embedding_function=self.text_embedding,
                                persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
                            )
        
        retriever = vector_store.as_retriever()
        
        docs = retriever.invoke(message)

        file_text = DEFAULT_DOCUMENT_SEPARATOR.join([format_document(doc, DEFAULT_DOCUMENT_PROMPT) for doc in docs])

        logging.info(f"User Context: {file_text}")


        match intention:

            case "General":
                response = await self.general.get_response(message=message, nusnet_id=nusnet_id, conversation_id=conversation_id, file_text=file_text)
                logging.info(f"General")

            case "Teaching":
                response = await self.teach.get_response(message=message, nusnet_id=nusnet_id, conversation_id=conversation_id, file_text=file_text)
                logging.info(f"Teaching")

            case "Guidance":
                response = await self.guide.get_response(message=message, nusnet_id=nusnet_id, conversation_id=conversation_id, file_text=file_text)
                logging.info(f"Guidance")


        return response
    
    # Response to document attachment
    async def global_load_document(self, file_path: str):

        loader = PyPDFLoader(file_path)
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)

        uuids = [str(uuid4()) for _ in range(len(splits))]



        # add documents to vectorstore
        await self.vector_store.aadd_documents(documents=splits, ids=uuids)
        self.retriever = self.vector_store.as_retriever()
        
    async def global_clear_documents(self):
        self.vector_store.reset_collection()


    

    # Response to document attachment
    async def load_document(self, file_path: str, nusnet_id: str):

        loader = PyPDFLoader(file_path)
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        splits = text_splitter.split_documents(docs)

        uuids = [str(uuid4()) for _ in range(len(splits))]

        vector_store = Chroma(
                                collection_name=nusnet_id,
                                embedding_function=self.text_embedding,
                                persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
                            )

        # add documents to vectorstore
        await vector_store.aadd_documents(documents=splits, ids=uuids)


    async def clear_documents(self, nusnet_id: str):

        vector_store = Chroma(
                                collection_name=nusnet_id,
                                embedding_function=self.text_embedding,
                                persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
                            )
        
        vector_store.reset_collection()