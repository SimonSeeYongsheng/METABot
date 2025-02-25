import random
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class DailyConversationInitiator:

    def __init__(self, llm, database):

        self.llm = llm
        self.database = database

        # Define a prompt that instructs the LLM to generate a creative conversation starter
        self.initiation_prompt = ChatPromptTemplate.from_messages([
            (
                "system", 
                "You are an AI conversation initiator. Using the user's recent chat history and the current time, generate a creative and engaging conversation starter question for today. "
                "Make sure to consider whether it's morning, afternoon, or evening, and tailor the tone accordingly."
                "If no conversation history is available, generate a generic yet engaging conversation starter question that invites the user to start a new conversation."
            ),
            (
                "human", 
                "Current time: {datetime}\n\n"
                "Chat history: {chat_history}\n\n"
                "Based on this context and chat message history, generate a daily conversation starter question"
            )
        ])
        # Create a chain that pipes the prompt to the LLM and then parses the output.
        self.initiation_chain = self.initiation_prompt | self.llm | StrOutputParser()

    async def initiate_conversation(self, user_id: str) -> str:
        """
        Retrieves the last 10 messages from the most recent conversation for the given user,
        generates a conversation starter using the LLM, and returns the generated prompt.
        """

        # Get the most recent conversation ID for the user.
        recent_convo_id = self.database.get_recent_conversation(user_id)
        messages = []
        if recent_convo_id:
            # Retrieve messages from the most recent conversation.
            messages.extend(self.database.get_by_session_id(user_id, recent_convo_id).messages)
            # Use the last 10 messages if available.
            last_ten_messages = messages[-5:] if messages else []
        else:
            last_ten_messages = []

        chat_history_text = last_ten_messages if last_ten_messages else "No previous messages available."

        print("History", chat_history_text)

        # Get the current time to add temporal context.
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Invoke the chain to generate a conversation starter, providing both chat history and datetime.
        result = self.initiation_chain.invoke({
            "chat_history": chat_history_text,
            "datetime": current_time
        })

        return result