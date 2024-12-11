# importing os module for environment variables
import os
# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 

load_dotenv() # Load environment variables from .env file

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chat_database
from langchain_chroma import Chroma
from uuid import uuid4

import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class Docs_DB:

    def __init__(self, text_embedding = None, text_splitter = None):

        if text_embedding == None:
            self.text_embedding = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        else:
            self.text_embedding = text_embedding

        if text_splitter == None:
            self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        else:
            self.text_splitter = text_splitter

    async def as_retriever(self, nusnet_id: str):

        vector_store = Chroma(
                                collection_name=nusnet_id,
                                embedding_function=self.text_embedding,
                                persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
                            )
        
        retriever = vector_store.as_retriever()
        return retriever

    async def load_document(self, file_path: str, nusnet_id: str):

        loader = PyPDFLoader(file_path)
        docs = loader.load()
        splits = self.text_splitter.split_documents(docs)

        logging.info(f"Loading docs...")

        uuids = [str(uuid4()) for _ in range(len(splits))]

        vector_store = Chroma(
                                collection_name=nusnet_id,
                                embedding_function=self.text_embedding,
                                persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
                            )

        # add documents to vectorstore
        lst_docs = await vector_store.aadd_documents(documents=splits, ids=uuids)

        logging.info(f"Added docs: {lst_docs}")


    async def clear_documents(self, nusnet_id: str):

        vector_store = Chroma(
                                collection_name=nusnet_id,
                                embedding_function=self.text_embedding,
                                persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
                            )
        
        vector_store.reset_collection()

        logging.info(f"Cleared docs for {nusnet_id}")

