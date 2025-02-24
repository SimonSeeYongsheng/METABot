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

        self.poll_details_collection_name = "poll_details"
        self.poll_details_collection = self.db[self.poll_details_collection_name]
        self.quiz_responses_collection_name = "quiz_responses"
        self.quiz_responses_collection = self.db[self.quiz_responses_collection_name]



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

    def get_all_students(self):
        # Query for documents where 'is_admin' is False and only return the 'user_id' field
        cursor = self.users_collection.find({"is_admin": False}, {"user_id": 1, "_id": 0})
        # Build a list of user_ids from the query results
        user_ids = [doc["user_id"] for doc in cursor if "user_id" in doc]
        return user_ids
    
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
    
    def store_poll_details(self, quiz_id: int, poll_id: str, question: str, correct_option_id: int, options: list, explanation: str):
        document = {
            "quiz_id": quiz_id,
            "poll_id": poll_id,
            "question": question,
            "correct_option_id": correct_option_id,
            "options": options,
            "explanation": explanation,
            "timestamp": datetime.now()
        }
        self.poll_details_collection.insert_one(document)

    def get_poll_details(self, poll_id: str):
        return self.poll_details_collection.find_one({"poll_id": poll_id})
    
    def get_latest_quiz_id(self):
    # Retrieve the latest quiz ID from the poll_details_collection

        latest_quiz = self.poll_details_collection.find_one(
            {},  # Find any document
            sort=[("quiz_id", -1)]  # Sort by quiz_id in descending order
        )
    
        return latest_quiz["quiz_id"] if latest_quiz else 0  # Return the latest quiz_id or 0 if none exist



    
    def store_quiz_response(self, quiz_id: int, poll_id: str, user_id: str, nusnet_id: str, student_answer: int,
                            question: str, correct_option_id: int, options: list, explanation: str,
                            is_correct: bool, timestamp: datetime):
        document = {
            "quiz_id": quiz_id,
            "poll_id": poll_id,
            "user_id": user_id,
            "nusnet_id": nusnet_id,
            "question": question,
            "options": options,
            "correct_option_id": correct_option_id,
            "student_answer": student_answer,
            "explanation": explanation,
            "is_correct": is_correct,
            "timestamp": timestamp
        }
        self.quiz_responses_collection.insert_one(document)

    def get_quiz_responses_by_student(self, nusnet_id: str):
        """Retrieve all quiz responses for a given student."""
        return list(self.quiz_responses_collection.find({"nusnet_id": nusnet_id}))
    
    def get_latest_mistakes_by_student(self, nusnet_id: str):
        # Retrieve mistakes from the latest quiz taken by the student.
        latest_quiz_id = self.get_latest_quiz_id()
        if latest_quiz_id == 0:
            return []  # No quizzes available

        # Query for incorrect responses from the latest quiz
        mistakes = list(self.quiz_responses_collection.find(
            {"nusnet_id": nusnet_id, "quiz_id": latest_quiz_id, "is_correct": False}
        ))

        return mistakes




    
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
        
    def export_quiz_responses_collection_to_csv(self, file_path: str):
        # Export the entire quiz responses collection to a CSV file.
        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # Query the quiz_responses collection
                cursor = self.quiz_responses_collection.find()
                first_doc = next(cursor, None)
                if not first_doc:
                    raise ValueError("No quiz responses to export.")
                headers = list(first_doc.keys())
                writer.writerow(headers)
                writer.writerow(list(first_doc.values()))
                for document in cursor:
                    writer.writerow(list(document.values()))
        except Exception as e:
            raise RuntimeError("Failed to export quiz responses collection.") from e










        


