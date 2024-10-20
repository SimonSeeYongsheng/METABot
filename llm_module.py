# importing os module for environment variables
import os
# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 

load_dotenv() # Load environment variables from .env file

from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory
# from langchain_openai import ChatOpenAI # (Can swap with Gemini AI)

from langchain_community.document_loaders import PyPDFLoader

# from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain_openai import OpenAIEmbeddings # (Can swap with Google Text Embedding)
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import ConfigurableFieldSpec
import database_module

from langchain_chroma import Chroma
from uuid import uuid4
from langchain_core.prompts import format_document
from langchain.chains.combine_documents.base import (
    DEFAULT_DOCUMENT_PROMPT,
    DEFAULT_DOCUMENT_SEPARATOR,
)

import logging

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
            
        
        self.llm = ChatGoogleGenerativeAI(model=self.model_name, 
                                          safety_settings=self.safety_settings,
                                          google_api_key=self.api_key)

        # self.llm = ChatOpenAI(model="gpt-4o-mini", api_key= os.environ.get('OPENAI_API_KEY'))

        self.vector_store = Chroma(
                                collection_name="global_doc_collection",
                                embedding_function=self.text_embedding,
                                persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
                            )

        
        # self.vector_store = InMemoryVectorStore(GoogleGenerativeAIEmbeddings(model=self.text_embedding))
        # self.vector_store = InMemoryVectorStore(embedding=OpenAIEmbeddings())
        self.retriever = self.vector_store.as_retriever(search_type="similarity_score_threshold",
                                                        search_kwargs={'score_threshold': 0.8})

        self.system_prompt = (

            "You are a highly knowledgeable and helpful AI assistant designed to provide accurate and detailed responses to user queries by utilizing both **Global Context** and **User Context** when available." 
            " Your purpose is to offer expert guidance and answers that are relevant, comprehensive, and clear." 
        )

        # self.system_prompt = (

        #     "You are an assistant that helps users by asking insightful questions instead of providing direct answers. " 
        #     "For every user query, your goal is to encourage the user to think critically and explore different angles of their question. "
        #     "Respond by asking guiding questions that prompt further reflection and discovery. \n\n"

        #     "Important instructions: \n"
        #     "1. Do NOT provide direct answers. \n"
        #     "2. Respond to the user by asking thought-provoking questions. \n"
        #     "3. Your questions should help the user understand the key components or steps they need to follow to find the solution themselves. \n\n"

        #     "Example: \n"
        #     "User: 'How do I fix a bug in my code?' \n"
        #     "Assistant: 'What specific part of your code is causing the issue? Have you tried isolating the problem by testing each function individually?' \n\n"

        #     "Make sure your responses remain in question format, aimed at guiding the user toward their own solution."
        #     "Keep the questions concise."
        # )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "Global context: {context}\n\nUser Context: {user_context}\n\nPrompt: {input}"),
            ]
        )
        self.question_answer_chain = create_stuff_documents_chain(self.llm, self.prompt)
        self.rag_chain = create_retrieval_chain(self.retriever, self.question_answer_chain)


        self.conversational_rag_chain = RunnableWithMessageHistory(
            self.rag_chain,
            self.database.get_by_session_id,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
            history_factory_config=[
                ConfigurableFieldSpec(
                    id="nusnet_id",
                    annotation=str,
                    name="User ID",
                    description="Unique identifier for the user.",
                    default="",
                    is_shared=True,
                ),
                ConfigurableFieldSpec(
                    id="conversation_id",
                    annotation=str,
                    name="Conversation ID",
                    description="Unique identifier for the conversation.",
                    default="",
                    is_shared=True,
                ),
            ],

        )

    # Response to text message    
    async def response_message(self, message: str, nusnet_id : str, conversation_id: str):

        vector_store = Chroma(
                                collection_name=nusnet_id,
                                embedding_function=self.text_embedding,
                                persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
                            )
        
        retriever = vector_store.as_retriever()
        
        docs = retriever.invoke(message)
        file_text = DEFAULT_DOCUMENT_SEPARATOR.join([format_document(doc, DEFAULT_DOCUMENT_PROMPT) for doc in docs])

        logging.info(f"User Context: {file_text}")


        config={
            "configurable": {"nusnet_id": nusnet_id , "conversation_id": conversation_id}
        }

        response = self.conversational_rag_chain.invoke({"input": message, "user_context": file_text},
                                                     config=config)

        return response['answer']
    
    # Response to document attachment
    async def global_load_document(self, file_path: str):

        loader = PyPDFLoader(file_path)
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)

        uuids = [str(uuid4()) for _ in range(len(splits))]



        # add documents to vectorstore
        await self.vector_store.aadd_documents(documents=splits, ids=uuids)
        self.retriever = self.vector_store.as_retriever(search_type="similarity_score_threshold",
                                                         search_kwargs={'score_threshold': 0.8})
        
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
        # self.retriever = self.vector_store.as_retriever(search_type="similarity_score_threshold",
        #                                                 search_kwargs={'score_threshold': 0.8})

    async def clear_documents(self, nusnet_id: str):

        vector_store = Chroma(
                                collection_name=nusnet_id,
                                embedding_function=self.text_embedding,
                                persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
                            )
        
        vector_store.reset_collection()