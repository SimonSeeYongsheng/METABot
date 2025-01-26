# importing os module for environment variables
import os
import shutil
# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 

load_dotenv() # Load environment variables from .env file

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from uuid import uuid4

import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class Prompts_DB:

    def __init__(self, chat_db, text_embedding = None):

        if text_embedding == None:
            self.text_embedding = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        else:
            self.text_embedding = text_embedding


        self.vector_store = Chroma(
                                collection_name="prompts_collection",
                                embedding_function=self.text_embedding,
                                persist_directory=f"./chroma_langchain_db",  # Where to save data locally, remove if not necessary
                            )
        
        documents_guide = chat_db.guide_responses_collection.find()

        for doc in documents_guide:

            unique_id = str(uuid4())

            self.vector_store.add_texts(
                texts=[doc.get("prompt")],
                metadatas=[{"assignment":doc.get("assignment"), "object_id": str(doc["_id"])}],
                ids=[unique_id]
            )

        documents_teach = chat_db.teach_responses_collection.find()

        for doc in documents_teach:

            unique_id = str(uuid4())

            self.vector_store.add_texts(
                texts=[doc.get("prompt")],
                metadatas=[{"assignment": "teach", "object_id": str(doc["_id"])}],
                ids=[unique_id]
            )

    def store_prompts(self, prompt: str, assignment: str, object_id: str):

        unique_id = str(uuid4())

        self.vector_store.add_texts(
            texts=[prompt],
            metadatas=[{"assignment":assignment, "object_id": object_id}],
            ids=[unique_id]
        )
        
    def query_prompts(self, user_query: str, assignment_filter: str):

        results = self.vector_store.similarity_search_with_relevance_scores(
            query=user_query,
            k=4,  # Number of results to return
            filter={"assignment": assignment_filter},  # Filter by assignment
            score_threshold=0.5 # Score threshold
        )
        if results:
            return list(map(lambda doc: doc[0].metadata.get("object_id"), results))
        else:
            return None




        




