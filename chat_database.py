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
import json


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
        self.guide_responses_collection_name = "guide_responses"
        self.teach_responses_collection_name = "teach_responses"

        # MongoDB connection setup
        self.client = MongoClient(self.MONGO_URI)
        self.db = self.client[self.database_name] # The name of the database
        self.users_collection = self.db[self.users_collection_name] # Collection to store user details
        self.chat_collection = self.db[self.chat_collection_name] # Collection to store chat history
        self.callback_collection = self.db[self.callback_collection_name] # Collection to store callback data
        self.guide_responses_collection = self.db[self.guide_responses_collection_name] # Collection to store guide responses
        self.teach_responses_collection = self.db[self.teach_responses_collection_name] # Collection to store teach responses

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
    
    def get_lab_group(self, user_id: str):
        user = self.users_collection.find_one({"user_id": user_id})
        return user.get("lab_group")
    
    def get_lab_students(self, lab_group: str):
        students = self.users_collection.find({"lab_group": lab_group, "is_admin": False})
        return students

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
        
        # If no conversation is found, return None
        return 1
    
    def get_callback_data_teach(self, object_id: str):

        object_id = ObjectId(object_id)

        # Query the document by _id
        document = self.callback_collection.find_one({"_id": object_id})
        prompt = document.get("prompt")
        response = document.get("response")
        
 
        return [prompt, response]
    
    def get_callback_data_guide(self, object_id: str):

        object_id = ObjectId(object_id)

        # Query the document by _id
        document = self.callback_collection.find_one({"_id": object_id})
        prompt = document.get("prompt")
        response = document.get("response")
        assignment = document.get("assignment")
 
        return [prompt, response, assignment]
    
    def get_saved_response_guide(self, list_object_id):

        best_response = None
        best_ratio = None
        best_like = None
        best_dislike = None
        best_object_id = None

        for object_id in list_object_id:

            obj_id = ObjectId(object_id)

            document = self.guide_responses_collection.find_one({"_id": obj_id})
            response = document.get("response")
            ratio = document.get("ratio")

            if best_response == None and best_ratio == None:
                best_response = response
                best_ratio = ratio
                best_like = document.get("like")
                best_dislike = document.get("dislike")
                best_object_id = object_id

            elif ratio > best_ratio:
                best_response = response
                best_ratio = ratio
                best_like = document.get("like")
                best_dislike = document.get("dislike")
                best_object_id = object_id

        return [best_object_id, best_response, best_like, best_dislike]
    
    def get_saved_response_teach(self, list_object_id):

        best_response = None
        best_ratio = None
        best_like = None
        best_dislike = None
        best_object_id = None

        for object_id in list_object_id:

            obj_id = ObjectId(object_id)

            document = self.teach_responses_collection.find_one({"_id": obj_id})
            response = document.get("response")
            ratio = document.get("ratio")

            if best_response == None and best_ratio == None:
                best_response = response
                best_ratio = ratio
                best_like = document.get("like")
                best_dislike = document.get("dislike")
                best_object_id = object_id

            elif ratio > best_ratio:
                best_response = response
                best_ratio = ratio
                best_like = document.get("like")
                best_dislike = document.get("dislike")
                best_object_id = object_id
                
        return [best_object_id, best_response, best_like, best_dislike]
        
    def get_all_conversation(self, nusnet_id: str):

        messages = []
        recent_convo_id = self.get_recent_conversation(nusnet_id=nusnet_id)

        if recent_convo_id:

            for convo_id in range(1, recent_convo_id + 1):
                messages.extend(self.get_by_session_id(nusnet_id=nusnet_id, conversation_id=convo_id).messages)
                
        return messages
    
    def start_new_conversation(self, message: str, nusnet_id: str):

        conversation_id = self.get_recent_conversation(nusnet_id) + 1

        chat_session_history = MongoDBChatMessageHistory(
                session_id={"nusnet_id": nusnet_id, "conversation_id": conversation_id},
                connection_string=self.MONGO_URI,
                database_name=self.database_name,
                collection_name=self.chat_collection_name,
                )

        chat_session_history.add_ai_message(message=message)

    def get_all_nusnet_ids(self):
        return self.users_collection.distinct("nusnet_id")
    
    def input_callback_data(self, prompt: str, response: str, assignment: str = None):

        if assignment:

            document = self.callback_collection.insert_one({
                "prompt" : prompt,
                "response" : response,
                "assignment" : assignment
            })
        
        else:

            document = self.callback_collection.insert_one({
                "prompt" : prompt,
                "response" : response,

            })
    
        return str(document.inserted_id)
    
    def input_feedback_teach(self, nusnet_id: str, prompt : str, response : str,  sentiment: str):

        document = self.teach_responses_collection.find_one({'prompt' : prompt})

        if document:

            match sentiment:

                case 'like':

                    if nusnet_id in document.get('like_users',[]):
                        return str(document.get('_id'))

                    elif nusnet_id in document.get('dislike_users',[]):
                        result = self.teach_responses_collection.update_one(
                            {'_id': document['_id']},
                            {
                                "$pull": {"dislike_users": nusnet_id},  # Remove user from 'dislike_users'
                                "$addToSet": {"like_users": nusnet_id},  # Add user to 'like_users'
                                "$inc": {"like": 1, "dislike": -1},  # Adjust counts
                                "$set": {"ratio": (document['like'] + 1) / (document['like'] + document['dislike'])}  # Update ratio
                            }
                        )
                        return str(result.upserted_id)

                    else:
                        result = self.teach_responses_collection.update_one(
                            {'_id': document['_id']},
                            {
                                "$addToSet": {"like_users": nusnet_id},  # Add user to 'like_users'
                                "$inc": {"like": 1},  # Increment 'like' count
                                "$set": {"ratio": (document['like'] + 1) / (document['like'] + document['dislike'] + 1)}  # Update ratio
                            }
                        )
                        return str(result.upserted_id)

                case 'dislike':

                    if nusnet_id in document.get('dislike_users',[]):
                        return str(document.get('_id'))
                    
                    elif nusnet_id in document.get('like_users',[]):
                        result = self.teach_responses_collection.update_one(
                            {'_id': document['_id']},
                            {
                                "$pull": {"like_users": nusnet_id},  # Remove user from 'like_users'
                                "$addToSet": {"dislike_users": nusnet_id},  # Add user to 'dislike_users'
                                "$inc": {"like": -1, "dislike": 1},  # Adjust counts
                                "$set": {"ratio": (document['like'] - 1) / (document['like'] + document['dislike'])}  # Update ratio
                            }
                        )
                        return str(result.upserted_id)

                    else:
                        result = self.teach_responses_collection.update_one(
                            {'_id': document['_id']},
                            {
                                "$addToSet": {"dislike_users": nusnet_id},  # Add user to 'dislike_users'
                                "$inc": {"dislike": 1},  # Increment 'dislike' count
                                "$set": {"ratio": document['like'] / (document['like'] + document['dislike'] + 1)}  # Update ratio
                            }
                        )
                        return str(result.upserted_id)
        else:
            match sentiment:

                case 'like':

                    result = self.teach_responses_collection.insert_one({
                        'prompt' : prompt,
                        'response' : response,
                        'like' : 1,
                        'dislike' : 0,
                        'ratio' : 1.0,
                        'like_users' : [nusnet_id],
                        'dislike_users' : [],
                        }
                    )
                    return str(result.inserted_id)
                
                case 'dislike':

                    result = self.teach_responses_collection.insert_one({
                        'prompt' : prompt,
                        'response' : response,
                        'like' : 0,
                        'dislike' : 1,
                        'ratio' : 0.0,
                        'like_users' : [],
                        'dislike_users' : [nusnet_id],
                        }
                    )
                    return str(result.inserted_id)
    
    def input_feedback_guide(self, nusnet_id: str, prompt : str, response : str, assignment: str, sentiment: str):

        document = self.guide_responses_collection.find_one({'assignment' : assignment, 'prompt' : prompt})

        if document:

            match sentiment:

                case 'like':

                    if nusnet_id in document.get('like_users',[]):
                        return str(document.get('_id'))

                    elif nusnet_id in document.get('dislike_users',[]):
                        result = self.guide_responses_collection.update_one(
                            {'_id': document['_id']},
                            {
                                "$pull": {"dislike_users": nusnet_id},  # Remove user from 'dislike_users'
                                "$addToSet": {"like_users": nusnet_id},  # Add user to 'like_users'
                                "$inc": {"like": 1, "dislike": -1},  # Adjust counts
                                "$set": {"ratio": (document['like'] + 1) / (document['like'] + document['dislike'])}  # Update ratio
                            }
                        )
                        return str(result.upserted_id)

                    else:
                        result = self.guide_responses_collection.update_one(
                            {'_id': document['_id']},
                            {
                                "$addToSet": {"like_users": nusnet_id},  # Add user to 'like_users'
                                "$inc": {"like": 1},  # Increment 'like' count
                                "$set": {"ratio": (document['like'] + 1) / (document['like'] + document['dislike'] + 1)}  # Update ratio
                            }
                        )
                        return str(result.upserted_id)

                case 'dislike':

                    if nusnet_id in document.get('dislike_users',[]):
                        return str(document.get('_id'))
                    
                    elif nusnet_id in document.get('like_users',[]):
                        result = self.guide_responses_collection.update_one(
                            {'_id': document['_id']},
                            {
                                "$pull": {"like_users": nusnet_id},  # Remove user from 'like_users'
                                "$addToSet": {"dislike_users": nusnet_id},  # Add user to 'dislike_users'
                                "$inc": {"like": -1, "dislike": 1},  # Adjust counts
                                "$set": {"ratio": (document['like'] - 1) / (document['like'] + document['dislike'])}  # Update ratio
                            }
                        )
                        return str(result.upserted_id)

                    else:
                        result = self.guide_responses_collection.update_one(
                            {'_id': document['_id']},
                            {
                                "$addToSet": {"dislike_users": nusnet_id},  # Add user to 'dislike_users'
                                "$inc": {"dislike": 1},  # Increment 'dislike' count
                                "$set": {"ratio": document['like'] / ( document['like'] + document['dislike'] + 1)}  # Update ratio
                            }
                        )
                        return str(result.upserted_id)
        else:
            match sentiment:

                case 'like':

                    result = self.guide_responses_collection.insert_one({
                        'assignment' : assignment,
                        'prompt' : prompt,
                        'response' : response,
                        'like' : 1,
                        'dislike' : 0,
                        'ratio' : 1,
                        'like_users' : [nusnet_id],
                        'dislike_users' : [],
                        }
                    )
                    return str(result.inserted_id)
                
                case 'dislike':

                    result = self.guide_responses_collection.insert_one({
                        'assignment' : assignment,
                        'prompt' : prompt,
                        'response' : response,
                        'like' : 0,
                        'dislike' : 1,
                        'ratio' : 0,
                        'like_users' : [],
                        'dislike_users' : [nusnet_id],
                        }
                    )
                    return str(result.inserted_id)

    def get_instructors(self, user_id: str):

        # Get lab group of user
        lab_group = self.get_lab_group(user_id=user_id)

        # Query the users collection for instructors of the user
        instructors = list(map(lambda x: x.get("user_id"), self.users_collection.find({ "lab_group": lab_group, "is_admin" :True}).to_list()))

        return instructors
    
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







        


