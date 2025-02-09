# importing os module for environment variables
import os
# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 

# importing MongoDB modules
from pymongo import MongoClient
from datetime import datetime
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
import csv
from bson.objectid import ObjectId

load_dotenv() # Load environment variables from .env file

class Chat_DB:
    def __init__(self, MONGO_URI: str = None, database_name: str = None, users_collection_name: str = None, chat_collection_name: str = None):

        if MONGO_URI == None:
            self.MONGO_URI = os.environ.get('MONGO_URI')
        if database_name == None:
            self.database_name = 'telegram_bot_db'
        if users_collection_name == None:
            self.users_collection_name = 'users'
        if chat_collection_name == None:
            self.chat_collection_name = 'chat_history'
   
        self.callback_collection_name = 'callback_collection'
        self.feedback_collection_name = "feedback_collection"

        # MongoDB connection setup
        self.client = MongoClient(self.MONGO_URI)
        self.db = self.client[self.database_name] # The name of the database
        self.users_collection = self.db[self.users_collection_name] # Collection to store user details
        self.chat_collection = self.db[self.chat_collection_name] # Collection to store chat history
        self.callback_collection = self.db[self.callback_collection_name] # Collection to store callback data
        self.feedback_collection = self.db[self.feedback_collection_name] # Collection to store feedback


    # Helper function to check if a user is authenticated
    def is_user_authenticated(self, user_id: str,telegram_handle: str):
        user = self.users_collection.find_one({"telegram_handle": telegram_handle})
        if user:
            if user.get("is_authenticated"):
                return True
            else:
                mongo_id = {'_id' : user.get("_id")}
                new_values = {
                                '$set': {
                                    "user_id": user_id,
                                    "is_authenticated": True,
                                    "joined_date": datetime.now()
                                    
                                }
                            }
                self.users_collection.update_one(mongo_id, new_values)
                return True
        return False
    
    # Helper function to check to get nusnet_id by user_id
    def get_nusnet_id(self, user_id: str):
        user = self.users_collection.find_one({"user_id": user_id})
        return user.get("nusnet_id")
    
    def user_exist(self, nusnet_id: str):
        user = self.users_collection.find_one({"nusnet_id": nusnet_id})
        return True if user else False
    
    def get_name(self, nusnet_id: str):
        user = self.users_collection.find_one({"nusnet_id": nusnet_id})
        return user.get("name")
    
    def is_admin(self, user_id: str):
        user = self.users_collection.find_one({"user_id": user_id})
        return user.get("is_admin")

    def get_by_session_id(self, nusnet_id: str, conversation_id: str) -> MongoDBChatMessageHistory:

        return MongoDBChatMessageHistory(
                session_id={"nusnet_id": nusnet_id, "conversation_id": conversation_id},
                connection_string=self.MONGO_URI,
                database_name=self.database_name,
                collection_name=self.chat_collection_name,
            )
    
    def get_recent_conversation(self, nusnet_id: str):

        # Query the chat collection for the most recent conversation of the given user
        recent_conversation = self.chat_collection.find({ "SessionId.nusnet_id": nusnet_id }).sort("SessionId.conversation_id", -1).limit(1).to_list()
  
        # If a conversation is found, return the conversation_id
        if len(recent_conversation) > 0:

            
            return recent_conversation[0].get("SessionId").get("conversation_id")
        
        # If no conversation is found, return 0
        return 0
    
    def get_callback_data(self, object_id: str):

        object_id = ObjectId(object_id)

        # Query the document by _id
        document = self.callback_collection.find_one({"_id": object_id})
        prompt = document.get("prompt")
        response = document.get("response")
        conversation_id = document.get("conversation_id")
        
 
        return [prompt, response, conversation_id]
        
    def get_all_conversation(self, nusnet_id: str):

        messages = []
        recent_convo_id = self.get_recent_conversation(nusnet_id=nusnet_id)

        if recent_convo_id:

            for convo_id in range(1, recent_convo_id + 1):
                messages.extend(self.get_by_session_id(nusnet_id=nusnet_id, conversation_id=convo_id).messages)
                
        return messages
    
    def add_human_message(self, message: str, nusnet_id: str):

        conversation_id = self.get_recent_conversation(nusnet_id)

        chat_session_history = MongoDBChatMessageHistory(
                session_id={"nusnet_id": nusnet_id, "conversation_id": conversation_id},
                connection_string=self.MONGO_URI,
                database_name=self.database_name,
                collection_name=self.chat_collection_name,
                )
        
        chat_session_history.add_user_message(message=message)
        
        return
    
    def add_ai_message(self, message: str, nusnet_id: str):

        conversation_id = self.get_recent_conversation(nusnet_id)

        chat_session_history = MongoDBChatMessageHistory(
                session_id={"nusnet_id": nusnet_id, "conversation_id": conversation_id},
                connection_string=self.MONGO_URI,
                database_name=self.database_name,
                collection_name=self.chat_collection_name,
                )
        
        chat_session_history.add_ai_message(message=message)
        
        return


    
    def start_new_conversation(self, message: str, nusnet_id: str):

        conversation_id = self.get_recent_conversation(nusnet_id) + 1

        chat_session_history = MongoDBChatMessageHistory(
                session_id={"nusnet_id": nusnet_id, "conversation_id": conversation_id},
                connection_string=self.MONGO_URI,
                database_name=self.database_name,
                collection_name=self.chat_collection_name,
                )

        chat_session_history.add_ai_message(message=message)

        return conversation_id

    def get_all_nusnet_ids(self):
        return self.users_collection.distinct("nusnet_id")
    
    def input_callback_data(self, prompt: str, response: str, conversation_id: int):

        document = self.callback_collection.insert_one({
                "prompt" : prompt,
                "response" : response,
                "conversation_id" : conversation_id,
        })

        return str(document.inserted_id)
    
    def input_feedback_data(self, prompt: str, response: str, conversation_id: int, nusnet_id: str, sentiment : str):

        document = self.feedback_collection.insert_one({
                "prompt" : prompt,
                "response" : response,
                "conversation_id" : conversation_id,
                "nusnet_id" : nusnet_id,
                "sentiment" : sentiment,
        })

        return str(document.inserted_id)
    
    def export_chat_collection_to_csv(self, file_path: str):
        # Export the entire chat collection to a CSV file.
        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # Write header row based on the keys of the documents
                cursor = self.chat_collection.find()
                first_doc = next(cursor, None)
                if not first_doc:
                    raise ValueError("No chat history to export.")
                
                headers = first_doc.keys()
                writer.writerow(headers)
                # Write data rows
                writer.writerow(first_doc.values())
                for document in cursor:
                    writer.writerow(document.values())

        except Exception as e:
            raise RuntimeError("Failed to export chat collection.") from e
        
    def export_feedback_collection_to_csv(self, file_path: str):
        # Export the entire chat collection to a CSV file.
        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # Write header row based on the keys of the documents
                cursor = self.feedback_collection.find()
                first_doc = next(cursor, None)
                if not first_doc:
                    raise ValueError("No teach feedback to export.")
                
                headers = first_doc.keys()
                writer.writerow(headers)
                # Write data rows
                writer.writerow(first_doc.values())
                for document in cursor:
                    writer.writerow(document.values())

        except Exception as e:
            raise RuntimeError("Failed to export teach feedback collection.") from e









        


