# importing os module for environment variables
import os
# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 

load_dotenv() # Load environment variables from .env file

# from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory (Can swap with ChatOpenAI)
from langchain_openai import ChatOpenAI # (Can swap with Gemini AI)
import chat_database


import logging
import analysis_module
import misconception_module
import teach_module
import mistake_module

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
            self.llm = ChatOpenAI(model="gpt-4o", api_key=os.environ.get('OPENAI_API_KEY'), temperature=0)
        else:
            self.llm = LLM

        if Chat_Database == None:
            self.chat_database = chat_database.Chat_DB()
        else:
            self.chat_database = Chat_Database

        self.analyse = analysis_module.Analyser(self.llm)
        self.misconception = misconception_module.Misconception(self.llm)
        self.teach = teach_module.Teacher(llm=self.llm, database=self.chat_database)
        self.mistake = mistake_module.Mistakes_Summariser(llm=self.llm)

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

        response = await self.analyse.get_analysis(name=name, nusnet_id=nusnet_id,
                                                    messages=messages)
        
        logging.info(f"Analysis report: {response}")
        
        return response
    
    # Response to misconception request
    async def misconception_message(self, nusnet_id : str):

        messages = self.chat_database.get_all_conversation(nusnet_id=nusnet_id)
        name = self.chat_database.get_name(nusnet_id=nusnet_id)

        response = await self.misconception.get_misconception(name=name, nusnet_id=nusnet_id,
                                                 messages=messages)
        
        logging.info(f"Misconception report: {response}")
        
        return response

    # Response to text message    
    async def response_message(self, message: str, nusnet_id : str, conversation_id: str, user_context: str):

        response = await self.teach.get_response(message=message, nusnet_id=nusnet_id, 
                                                         conversation_id=conversation_id, user_context = user_context)
        logging.info(f"Teaching: {response}")

        return response
    
    # Response to mistake summary request
    async def mistake_message(self, mistakes: str):

        response = await self.mistake.get_summary(message=mistakes)

        logging.info(f"Msitakes: {response}")

        return response




