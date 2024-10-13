# importing os module for environment variables
import os
# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 

load_dotenv() # Load environment variables from .env file

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings, HarmBlockThreshold, HarmCategory

from langchain_community.document_loaders import PyPDFLoader

from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain_openai import OpenAIEmbeddings (Can swap with Google Text Embedding)
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory

MONGO_URI = os.environ.get('MONGO_URI')
database_name = 'telegram_bot_db'
chat_collection_name = 'chat_history'

class LLM:
    def __init__(self, model_name: str = None, safety_settings: dict = None, api_key: str = None, text_embedding: str = None):

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
            self.text_embedding = "models/text-embedding-004"
            
        
        self.llm = ChatGoogleGenerativeAI(model=self.model_name, 
                                          safety_settings=self.safety_settings,
                                          google_api_key=self.api_key)
        

        self.vector_store = InMemoryVectorStore(GoogleGenerativeAIEmbeddings(model=self.text_embedding))
        self.retriever = self.vector_store.as_retriever()

        self.contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )

        self.contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        self.system_prompt = (
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know. Keep the answer concise."
            "\n\n"
            "{context}"
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                #MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        self.history_aware_retriever = create_history_aware_retriever(self.llm, self.retriever, self.contextualize_q_prompt)

        self.question_answer_chain = create_stuff_documents_chain(self.llm, self.prompt)
        #self.rag_chain = create_retrieval_chain(self.history_aware_retriever, self.question_answer_chain)
        self.rag_chain = create_retrieval_chain(self.retriever, self.question_answer_chain)

        

        self.conversational_rag_chain = RunnableWithMessageHistory(
            self.rag_chain,
            lambda session_id: MongoDBChatMessageHistory(
                session_id=session_id,
                connection_string=MONGO_URI,
                database_name=database_name,
                collection_name=chat_collection_name,
            ),
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

    # Response to text message    
    async def response_message(self, message: str, user_id: str):


        config={
            "configurable": {"session_id": user_id}
        }
        # return self.conversational_rag_chain.invoke({"input": message},
        #                                             config=config)['answer']

        return self.rag_chain.invoke({"input": message})['answer']


    

    # Response to document attachment
    async def load_document(self, file_path: str):

        # config={
        #     "configurable": {"session_id": user_id}
        # }

        loader = PyPDFLoader(file_path)
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)

        # add documents to vectorstore
        await self.vector_store.aadd_documents(documents=splits)
