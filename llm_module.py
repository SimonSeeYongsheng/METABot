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
import chat_database


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
# import intent_classifier
import analysis_module
import sitrep_module
import general_module
import guidance_module
import teach_module
import assignment_classifier

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

MONGO_URI = os.environ.get('MONGO_URI')
database_name = 'telegram_bot_db'
chat_collection_name = 'chat_history'

class LLM:
    def __init__(self, LLM = None, Chat_Database = None):


        if LLM == None:
            self.llm = ChatOpenAI(model="gpt-4o-mini", api_key= os.environ.get('OPENAI_API_KEY'))
        else:
            self.llm = LLM

        if Chat_Database == None:
            self.chat_database = chat_database.Chat_DB()
        else:
            self.chat_database = Chat_Database



        
        # self.intent = intent_classifier.Intent_Classifier(self.llm)
        self.assignment = assignment_classifier.Assignment_Classifier(self.llm)
        self.analyse = analysis_module.Analyser(self.llm)
        self.sitrep = sitrep_module.Sitrep(self.llm)
        self.general = general_module.General(llm=self.llm, database=self.chat_database)
        self.teach = teach_module.Teacher(llm=self.llm, database=self.chat_database)
        self.guide = guidance_module.Guide(llm=self.llm, database=self.chat_database)

        
        # self.vector_store = InMemoryVectorStore(GoogleGenerativeAIEmbeddings(model=self.text_embedding))
        # self.vector_store = InMemoryVectorStore(embedding=OpenAIEmbeddings())

    # Response to assignment classification
    async def assignment_message(self, message : str):

        list_assignments = self.chat_database.get_assignments()

        assignment_name = await self.assignment.get_assignment(message=message,
                                                                list_assignments=list_assignments)

        logging.info(f"Assignment: {assignment_name}")

        return assignment_name


    # Response to analysis request
    async def analyse_message(self, nusnet_id : str):

        messages = self.chat_database.get_all_conversation(nusnet_id=nusnet_id)
        name = self.chat_database.get_name(nusnet_id=nusnet_id)

        response = await self.analyse.get_analysis(name=name, nusnet_id=nusnet_id, messages=messages)
        
        logging.info(f"Analysis report: {response}")
        
        return response
    
    # Response to sitrep request
    async def sitrep_message(self, nusnet_id : str):

        messages = self.chat_database.get_all_conversation(nusnet_id=nusnet_id)
        name = self.chat_database.get_name(nusnet_id=nusnet_id)

        print("Messages", messages)

        response = await self.sitrep.get_sitrep(name=name, nusnet_id=nusnet_id, messages=messages)
        
        logging.info(f"Sitrep report: {response}")
        
        return response




    # Response to text message    
    async def response_message(self, message: str, nusnet_id : str, conversation_id: str, intention: str, user_context: str):

        logging.info(f"Intent report: {intention}")

        match intention:

            # case "general":
            #     response = await self.general.get_response(message=message, nusnet_id=nusnet_id, conversation_id=conversation_id)
            #     logging.info(f"General: {response}")

            case "guide":
                response = await self.guide.get_response(message=message, nusnet_id=nusnet_id, conversation_id=conversation_id,user_context = user_context)

            case "teach":
                response = await self.teach.get_response(message=message, nusnet_id=nusnet_id, conversation_id=conversation_id, user_context = user_context)
                logging.info(f"Teaching: {response}")

        return response

