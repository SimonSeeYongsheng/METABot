# importing os module for environment variables
import os
# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 

load_dotenv() # Load environment variables from .env file

from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory
from langchain_openai import ChatOpenAI # (Can swap with Gemini AI)

from langchain_community.document_loaders import PyPDFLoader

# from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain_openai import OpenAIEmbeddings # (Can swap with Google Text Embedding)
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import ConfigurableFieldSpec
import database_module

from langchain_chroma import Chroma
from uuid import uuid4
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import format_document
from langchain.chains.combine_documents.base import (
    DEFAULT_DOCUMENT_PROMPT,
    DEFAULT_DOCUMENT_SEPARATOR,
)

import logging
from datetime import datetime

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

MONGO_URI = os.environ.get('MONGO_URI')
database_name = 'telegram_bot_db'
chat_collection_name = 'chat_history'

class LLM:
    def __init__(self, model_name: str = None, safety_settings: dict = None, api_key: str = None, text_embedding: str = None, database = None):

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
            self.text_embedding = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

        if database == None:
            self.database = database_module.DB()
            
        
        self.llm = ChatGoogleGenerativeAI(model=self.model_name, 
                                          safety_settings=self.safety_settings,
                                          google_api_key=self.api_key)

        self.llm = ChatOpenAI(model="gpt-4o-mini", api_key= os.environ.get('OPENAI_API_KEY'))

        self.vector_store = Chroma(
                                collection_name="global_doc_collection",
                                embedding_function=self.text_embedding,
                                persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
                            )

        
        # self.vector_store = InMemoryVectorStore(GoogleGenerativeAIEmbeddings(model=self.text_embedding))
        # self.vector_store = InMemoryVectorStore(embedding=OpenAIEmbeddings())
        self.retriever = self.vector_store.as_retriever(search_type="similarity_score_threshold",
                                                        search_kwargs={'score_threshold': 0.5})
        
        self.anaylse_system_prompt = (
"""
You are an AI tasked with analyzing the chat history between a user and an educational chatbot to provide detailed insights into the user's learning abilities. Specifically, your goal is to differentiate between surface-level learning (basic understanding and memorization) and higher-order learning (critical thinking, problem-solving, and application). You will also analyze key themes, topics, or concepts from the user's most recent interactions. The report should begin with the following format:

"Here is a learning analytics report of {nusnet_id}, {name} as of {datetime}"

**If no chat history is available for this user, respond with:**
"There is no chat history available for {nusnet_id}, {name} as of {datetime}. Therefore, no learning analysis can be provided at this time."

If chat history exists, follow these guidelines to generate the report:

1. **Assess Learning Depth:**
   - **Surface-Level Learning**: Identify instances where the user demonstrates a basic, factual understanding of concepts, focusing on recall or memorization (e.g., asking for definitions, straightforward answers, or relying on rote learning).
   - **Higher-Order Learning**: Identify moments where the user exhibits deeper learning, such as applying concepts to new problems, analyzing and synthesizing information, or demonstrating critical thinking (e.g., asking how, why, or what-if questions, connecting concepts, or exploring implications).

2. **Analyze Key Themes, Topics, or Concepts:**
   - Identify the key themes, topics, or concepts from the user’s most recent interactions with the chatbot. Look for recurring subjects (e.g., algorithms, programming, mathematics) or specific concepts (e.g., recursion, sorting algorithms, dynamic programming) that the user has focused on.
   - Highlight which of these topics the user has engaged with deeply (indicating higher-order learning) versus those where they showed surface-level understanding or struggled.

3. **Analyze User’s Problem-Solving Approach:**
   - **Surface-Level Problem-Solving**: Look for cases where the user seeks direct answers or step-by-step instructions without attempting to think through the problem independently.
   - **Higher-Order Problem-Solving**: Identify instances where the user demonstrates strategic thinking, tries to work through problems independently, or engages in self-directed exploration before seeking help.

4. **Learning Behavior Insights:**
   - **Surface-Level Behavior**: Highlight areas where the user shows reliance on repetition or lacks depth in responses (e.g., asking the same question multiple times without showing progress or simply restating provided information).
   - **Higher-Order Behavior**: Highlight areas where the user engages with content more deeply, showing progress in understanding complex concepts, making connections between ideas, or seeking to explore a concept beyond what is taught (e.g., discussing applications, seeking extensions of knowledge).

5. **Learning Engagement and Motivation:**
   - **Surface-Level Engagement**: Identify if the user shows passive engagement, such as only interacting when prompted, or seeking only quick answers to finish a task.
   - **Higher-Order Engagement**: Look for active engagement patterns, such as asking open-ended questions, initiating deep discussions, or showing enthusiasm for learning beyond task requirements.

6. **Provide Recommendations for Learning Development:**
   - **For Surface-Level Learners**: Suggest strategies to move beyond rote memorization, such as focusing on the "why" behind concepts, engaging in active problem-solving exercises, or exploring case studies to apply knowledge.
   - **For Higher-Order Learners**: Recommend more challenging tasks, such as solving real-world problems, exploring interdisciplinary applications, or engaging in research-based learning to deepen critical thinking.

7. **Summary of Learning Progress and Ability:**
   - Provide a summary that identifies whether the user primarily exhibits surface-level learning, higher-order learning, or a mixture of both.
   - Include the key themes, topics, or concepts the user has focused on in recent interactions, noting whether the user demonstrated surface-level or higher-order learning for each topic.
   - Highlight any notable shifts in learning behavior over time, and suggest a pathway for encouraging the user to move towards deeper learning and critical thinking skills.
"""
        )

        self.system_prompt = (
"""
You are an AI tutor designed to teach users about knowledge content, concepts, and problem-solving strategies. Follow these strict rules when interacting with users:

**Note**: Ensure the entire reponse does not exceed 4096 characters.

1. **For Conceptual or Knowledge-Based Questions:**
   - Provide clear, detailed explanations to teach or clarify the user's query.
   - Use examples or analogies when necessary to aid understanding.

2. **For Problem-Solving or Direct Answer Requests:**
   - **Do NOT provide direct answers or solutions** to problem-solving questions. Under no circumstances should you state which algorithm, method, or solution is the best or correct one.
   - **Instead, only offer hints and guiding questions**. Your goal is to prompt the user to think through the problem themselves by considering key aspects.
   - Use **ONLY** scaffolding phrases like: "Have you considered...", "What do you think about...", "Can you break the problem into smaller steps?", "What constraints could influence the choice of solution?", "What are the memory trade-offs you might want to consider?"
   - Avoid naming specific algorithms or solutions. Focus solely on guiding the thought process.

3. **Ensure that users engage in the problem-solving process** by encouraging them to reflect on their approach, rather than giving them any answers or solutions.

Your role is to help users develop critical thinking and problem-solving skills by guiding their approach, not by providing them with the solutions.
"""
        )

        # self.system_prompt = (

        #     "You are an assistant that helps users by asking insightful questions instead of providing direct answers. " 
        #     "For every user query, your goal is to encourage the user to think critically and explore different angles of their question. "
        #     "Respond by asking guiding questions that prompt further reflection and discovery. \n\n"

        #     "Important instructions: \n"
        #     "1. Do NOT provide direct answers. \n"
        #     "2. Respond to the user by asking thought-provoking questions. \n"
        #     "3. Your questions should help the user understand the key components or steps they need to follow to find the solution themselves. \n\n"

        #     "Example: \n"
        #     "User: 'How do I fix a bug in my code?' \n"
        #     "Assistant: 'What specific part of your code is causing the issue? Have you tried isolating the problem by testing each function individually?' \n\n"

        #     "Make sure your responses remain in question format, aimed at guiding the user toward their own solution."
        #     "Keep the questions concise."
        # )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "Global context: {context}\n\nUser Context: {user_context}\n\nPrompt: {input}"),
            ]
        )

        self.anaylse_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.anaylse_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "Give me a learning analysis report of the user using the previous chat history.\
                  **Note**: Ensure the entire response does not exceed 4096 characters.")
            ]
        )

        self.question_answer_chain = create_stuff_documents_chain(self.llm, self.prompt)
        self.rag_chain = create_retrieval_chain(self.retriever, self.question_answer_chain)

        self.analyse_chain = self.anaylse_prompt | self.llm | StrOutputParser()


        self.conversational_rag_chain = RunnableWithMessageHistory(
            self.rag_chain,
            self.database.get_by_session_id,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
            history_factory_config=[
                ConfigurableFieldSpec(
                    id="nusnet_id",
                    annotation=str,
                    name="User ID",
                    description="Unique identifier for the user.",
                    default="",
                    is_shared=True,
                ),
                ConfigurableFieldSpec(
                    id="conversation_id",
                    annotation=str,
                    name="Conversation ID",
                    description="Unique identifier for the conversation.",
                    default="",
                    is_shared=True,
                ),
            ],

        )

    # Response to analysis request
    async def analyse_message(self, nusnet_id : str):

        messages = self.database.get_all_conversation(nusnet_id=nusnet_id)
        name = self.database.get_name(nusnet_id=nusnet_id)

        response = self.analyse_chain.invoke({"nusnet_id": nusnet_id, "name": name, 
                                              "datetime": datetime.now(), "chat_history": messages})
        
        logging.info(f"Analysis report: {response}")
        
        return response




    # Response to text message    
    async def response_message(self, message: str, nusnet_id : str, conversation_id: str):

        vector_store = Chroma(
                                collection_name=nusnet_id,
                                embedding_function=self.text_embedding,
                                persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
                            )
        
        retriever = vector_store.as_retriever()
        
        docs = retriever.invoke(message)
        file_text = DEFAULT_DOCUMENT_SEPARATOR.join([format_document(doc, DEFAULT_DOCUMENT_PROMPT) for doc in docs])

        logging.info(f"User Context: {file_text}")


        config={
            "configurable": {"nusnet_id": nusnet_id , "conversation_id": conversation_id}
        }

        response = self.conversational_rag_chain.invoke({"input": message, "user_context": file_text},
                                                     config=config)

        return response['answer']
    
    # Response to document attachment
    async def global_load_document(self, file_path: str):

        loader = PyPDFLoader(file_path)
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)

        uuids = [str(uuid4()) for _ in range(len(splits))]



        # add documents to vectorstore
        await self.vector_store.aadd_documents(documents=splits, ids=uuids)
        self.retriever = self.vector_store.as_retriever(search_type="similarity_score_threshold",
                                                         search_kwargs={'score_threshold': 0.5})
        
    async def global_clear_documents(self):
        self.vector_store.reset_collection()


    

    # Response to document attachment
    async def load_document(self, file_path: str, nusnet_id: str):

        loader = PyPDFLoader(file_path)
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        splits = text_splitter.split_documents(docs)

        uuids = [str(uuid4()) for _ in range(len(splits))]

        vector_store = Chroma(
                                collection_name=nusnet_id,
                                embedding_function=self.text_embedding,
                                persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
                            )

        # add documents to vectorstore
        await vector_store.aadd_documents(documents=splits, ids=uuids)


    async def clear_documents(self, nusnet_id: str):

        vector_store = Chroma(
                                collection_name=nusnet_id,
                                embedding_function=self.text_embedding,
                                persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
                            )
        
        vector_store.reset_collection()