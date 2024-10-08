# importing os module for environment variables
import os
# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 

# importing MongoDB modules
from pymongo import MongoClient
from datetime import datetime

load_dotenv() # Load environment variables from .env file

# MONGO_URI = os.environ.get('MONGO_URI')

# # MongoDB connection setup
# client = MongoClient(MONGO_URI)
# db = client['telegram_bot_db'] # The name of the database
# users_collection = db['users'] # Collection to store user details
# chat_collection = db['chat_history'] # Collection to store chat history

class DB:
    def __init__(self, MONGO_URI: str = None, database_name: str = None, users_collection_name: str = None, chat_collection_name: str = None):

        if MONGO_URI == None:
            MONGO_URI = os.environ.get('MONGO_URI')
        if database_name == None:
            database_name = 'telegram_bot_db'
        if users_collection_name == None:
            users_collection_name = 'users'
        if chat_collection_name == None:
            chat_collection_name = 'chat_history'
        

        # MongoDB connection setup
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[database_name] # The name of the database
        self.users_collection = self.db[users_collection_name] # Collection to store user details
        self.chat_collection = self.db[chat_collection_name] # Collection to store chat history

    # Helper function to check if a user is authenticated
    def is_user_authenticated(self, user_id: str):
        user = self.users_collection.find_one({"user_id": user_id})
        if user and user.get("is_authenticated"):
            return True
        return False

    # Helper function to authenticate a user
    def authenticate_user(self, user_id: str, telegram_handle: str):
        if not self.users_collection.find_one({"user_id": user_id}):
            self.users_collection.insert_one({
                "user_id": user_id,
                "telegram_handle": telegram_handle,
                "is_authenticated": True,
                "joined_date": datetime.now()
            })

    # Function to log chat history
    def log_chat(self, user_id: str, telegram_handle: str, message: str, response: str):
        self.chat_collection.insert_one({
            "user_id": user_id,
            "telegram_handle": telegram_handle,
            "message": message,
            "response": response,
            "timestamp": datetime.now()
        })
