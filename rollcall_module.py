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
    *Here is a rollcall report of {nusnet_id}, {name} as of {datetime}:*

    **If no chat history is available for this user, respond with:**
    *There is no chat history available for {nusnet_id}, {name} as of {datetime}. Therefore, no rollcall report can be provided at this time.*

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
    User: *How do I calculate factorials using recursion?*
    Bot: *Recursion involves a function calling itself. Are you familiar with base cases?*
    User: *Not really. What are they for?*

    Output:
    - **Topic**: _Understanding recursion in Python, specifically base cases._
    - **Key Details**: _The user asked about the purpose of base cases in recursion._
    - **Next Steps**: _Provide a simple example explaining base cases._

    **Formatting in Telegram Bot Legacy Markdown**:
    - Use `*bold*` for emphasis.
    - Use `_italic_` for additional emphasis or alternative text.
    - Use `\`inline code\`` for short code snippets.
    - Use triple backticks (```) for blocks of code or preformatted text, specifying the language for syntax highlighting (e.g., ```javascript).

    **Special Character Escaping**:
    - To escape characters `_`, `*`, `` ` ``, `[` outside of an entity, prepend the characters `\` before them.
    - Escaping inside entities is not allowed, so an entity must be closed first and reopened again: 
        - Use `_snake_\__case_` for italic *snake_case*.
        - Use `*2*\**2=4*` for bold *2*2=4.

    Always ensure your analysis is precise, concise, and relevant to the user's recent messages while adhering to the Telegram bot legacy Markdown format.
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
