# importing os module for environment variables
import os
import shutil
# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 

load_dotenv() # Load environment variables from .env file

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import BSHTMLLoader
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PythonLoader

import chat_database
from chromadb.errors import ChromaError
from langchain_chroma import Chroma
from uuid import uuid4

import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class Docs_DB:

    def __init__(self, text_embedding = None, text_splitter = None, Chat_Database = None):

        if text_embedding == None:
            self.text_embedding = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        else:
            self.text_embedding = text_embedding

        if text_splitter == None:
            self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        else:
            self.text_splitter = text_splitter

        if Chat_Database == None:
            self.chat_database = chat_database.Chat_DB()
        else:
            self.chat_database = Chat_Database

    async def as_retriever(self, nusnet_id: str):

        vector_store = Chroma(
                                collection_name=nusnet_id,
                                embedding_function=self.text_embedding,
                                persist_directory=f"./chroma_langchain_db/{nusnet_id}",  # Where to save data locally, remove if not necessary
                            )
        
        retriever = vector_store.as_retriever()
        return retriever

    async def load_document(self, file_path: str, nusnet_id: str, file_type: str):
        try:
            # Initialize the vector store
            vector_store = Chroma(
                collection_name=nusnet_id,
                embedding_function=self.text_embedding,
                persist_directory=f"./chroma_langchain_db/{nusnet_id}",
            )

            # Determine file type and process accordingly
            match file_type:

                case "PDF":
                    try:
                        loader = PyPDFLoader(file_path)
                        docs = loader.load()
                    except Exception as e:
                        logging.error(f"Error loading PDF file: {e}")
                        raise ValueError(f"Failed to process PDF file: {file_path}")

                case "HTML":
                    try:
                        loader = BSHTMLLoader(file_path)
                        docs = loader.load()
                    except Exception as e:
                        logging.error(f"Error loading HTML file: {e}")
                        raise ValueError(f"Failed to process HTML file: {file_path}")
                    
                case "PY":
                    try:
                        loader = PythonLoader(file_path)  
                        docs = loader.load()
                    except Exception as e:
                        logging.error(f"Error loading Python file: {e}")
                        raise ValueError(f"Failed to process Python file: {file_path}")

                case _:
                    try:
                        loader = TextLoader(file_path)
                        docs = loader.load()
                    except Exception as e:
                        logging.error(f"Error loading text file: {e}")
                        raise ValueError(f"Failed to process text file: {file_path}")

            # Split documents
            try:
                splits = self.text_splitter.split_documents(docs)
            except Exception as e:
                logging.error(f"Error splitting documents: {e}")
                raise ValueError(f"Failed to split documents for file: {file_path}")

            logging.info(f"Loading docs...")

            # Generate unique IDs for the splits
            uuids = [str(uuid4()) for _ in range(len(splits))]

            # Add documents to vectorstore
            try:
                lst_docs = await vector_store.aadd_documents(documents=splits, ids=uuids)
                logging.info(f"Added docs: {lst_docs}")
            except Exception as e:
                logging.error(f"Error adding documents to vectorstore: {e}")
                raise ValueError(f"Failed to add documents to vectorstore for file: {file_path}")

        except Exception as e:
            logging.error(f"Unexpected error in load_document: {e}")
            raise

        finally:
            # Ensure file is removed even if an error occurs
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logging.info(f"Removed file: {file_path}")
                except Exception as e:
                    logging.error(f"Error removing file: {file_path}. {e}")

    def clear_documents(self, nusnet_id: str):
        try:
            # Initialize Chroma vector store
            vector_store = Chroma(
                collection_name=nusnet_id,
                embedding_function=self.text_embedding,
                persist_directory=f"./chroma_langchain_db/{nusnet_id}",
            )
            
            # Attempt to delete the collection
            try:
                vector_store.delete_collection()
                logging.info(f"Deleted collection for {nusnet_id}.")
            except ChromaError as e:
                logging.error(f"Failed to delete collection for {nusnet_id}: {e}")
                raise RuntimeError(f"Error deleting collection for {nusnet_id}.") from e

            # Attempt to remove the directory
            try:
                shutil.rmtree(f"./chroma_langchain_db/{nusnet_id}", ignore_errors=True)
                logging.info(f"Removed directory for {nusnet_id}.")
            except OSError as e:
                logging.error(f"Failed to remove directory for {nusnet_id}: {e}")
                raise RuntimeError(f"Error removing directory for {nusnet_id}.") from e

            logging.info(f"Successfully cleared docs for {nusnet_id}.")

        except Exception as e:
            logging.error(f"An error occurred while clearing documents for {nusnet_id}: {e}")
            raise RuntimeError(f"An unexpected error occurred while clearing documents for {nusnet_id}.") from e
        
    def clear_all_docs(self):

        list_nusnet_id = self.chat_database.get_all_nusnet_ids()

        for nusnet_id in list_nusnet_id:

            self.clear_documents(nusnet_id=nusnet_id)

        




