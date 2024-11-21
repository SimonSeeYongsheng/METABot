from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from datetime import datetime


class Rollcall:

    def __init__(self, llm):

        self.llm = llm
        self.rollcall_system_prompt = (
            """
            You are an AI assistant tasked with analyzing the most recent topic of discussion from a provided chat history. 
            Your primary objectives are:

            1. **Identify the Topic**: Determine the main subject of the user's most recent conversation.
            2. **Provide a Concise Summary**: Summarize the topic clearly in one to two sentences.
            3. **Highlight Key Details**: Include only critical points or questions from the recent exchanges.

            The report should begin with the following format:
            "Here is a rollcall report of {nusnet_id}, {name} as of {datetime}:"

            **If no chat history is available for this user, respond with:**
            "There is no chat history available for {nusnet_id}, {name} as of {datetime}. Therefore, no rollcall report can be provided at this time."

            If chat history exists, follow these guidelines to generate the report:
            - Review the chat history from the most recent to earlier messages.
            - Focus only on the last few exchanges that are topically related.
            - Avoid unnecessary explanations or redundant information.
            - If the topic is unclear, briefly suggest potential interpretations or request clarification.
            - Do not include personal opinions or assumptions not supported by the chat content.

            **Output Format**:
            - **Topic**: [Brief description of the main topic]\n\n
            - **Key Details**: [Essential points or questions raised]\n\n
            - **Next Steps (Optional)**: [Follow-up action or clarification if needed]

            **Example**:
            Chat History:
            User: "How do I calculate factorials using recursion?"
            Bot: "Recursion involves a function calling itself. Are you familiar with base cases?"
            User: "Not really. What are they for?"

            Output:
            - **Topic**: Understanding recursion in Python, specifically base cases.
            - **Key Details**: The user asked about the purpose of base cases in recursion.
            - **Next Steps**: Provide a simple example explaining base cases.

            Always ensure your analysis is precise, concise, and relevant to the user's recent messages.
            """
        )

        
        self.rollcall_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.rollcall_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "Give me a rollcall report of the user using the previous chat history.\
                  **Note**: Ensure the entire response does not exceed 4096 characters.")
            ]
        )

        self.rollcall_chain = self.rollcall_prompt | self.llm | StrOutputParser()

    async def get_rollcall(self, name : str, nusnet_id : str, messages):

        response = self.rollcall_chain.invoke({"nusnet_id": nusnet_id, "name": name, 
                                              "datetime": datetime.now().replace(microsecond=0), "chat_history": messages})
    
        return response
