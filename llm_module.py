# importing os module for environment variables
import os
# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 

load_dotenv() # Load environment variables from .env file

from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory

class LLM:
    def __init__(self, model_name: str = None, safety_settings: dict = None, api_key: str = None):

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
            
        
        self.llm = ChatGoogleGenerativeAI(model=self.model_name, 
                                          safety_settings=self.safety_settings,
                                          google_api_key=self.api_key)
        
    def response(self, message: str):
        return self.llm.invoke(message).content

