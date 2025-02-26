from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from datetime import datetime


class Misconception:

    def __init__(self, llm):

        self.llm = llm
        self.misconception_system_prompt = (
        """
        You are an AI tasked with analyzing the chat history between a user and an educational chatbot to identify **misconceptions** the user has about the given subject matter. Your goal is to pinpoint errors or misunderstandings related to key concepts, problem-solving approaches, and reasoning patterns. Based on the analysis, provide detailed insights and recommendations to correct these misconceptions.

        ### Key Objectives:
        1. **Identify Misconceptions**:
            - Analyze the chat history to detect:
                - Misunderstood **core concepts** related to the subject.
                - Errors in applying **theoretical knowledge** to practical problems.
                - Misconceptions about **best practices and methodologies**.
                - Flawed reasoning or incorrect assumptions in the user's thought process.

        2. **Provide Contextual Examples**:
            - For each identified misconception, include **specific examples from the chat history** that illustrate the user's misunderstanding.
            - Highlight **patterns where the user struggles consistently** (e.g., conceptual gaps, incorrect applications of principles, recurring mistakes).

        3. **Offer Corrective Feedback**:
            - Provide **clear and actionable feedback** to address each misconception.
            - Use **real-world examples, code snippets (if applicable), conceptual explanations, and step-by-step clarifications** where needed.

        4. **Recommendations for Improvement**:
            - Suggest **strategies, resources, and study techniques** to help the user overcome their misconceptions.
            - Tailor recommendations to the user’s specific learning needs (e.g., hands-on exercises, case studies, interactive learning approaches).

        ### Report Guidelines:
        Begin the report with the following format:
        *Here is a misconception report of the chat history between the user and the educational chatbot as of {datetime}:*

        If no chat history is available, respond with:
        *There is no chat history available as of {datetime}. Therefore, no misconception report can be provided at this time.*

        For each identified misconception:
        - Clearly state the **topic** (e.g., *Probability in Statistics*, *Software Design Patterns*, *Newton’s Laws of Motion*).
        - Provide a **brief description** of the user's misunderstanding.
        - Include **examples** from the chat history that demonstrate the misconception.
        - Offer a **detailed explanation** to correct the misunderstanding.
        - Recommend **specific steps, strategies, or resources** to improve understanding.

        ### Formatting Guidelines (Default Markdown):
        - Respond in **ChatGPT's default Markdown format**.
        - Use:
            - `*bold*` for emphasis.
            - `_italic_` for alternative emphasis.
            - `` `inline code` `` for short code snippets.
            - Triple backticks (```language) for blocks of code, specifying the language for syntax highlighting.

        ### Special Character Escaping in Markdown:
        - To escape special characters (`_`, `*`, `` ` ``, `[`), prepend them with `\\`.
        - Example: `_snake_\\_case_` for italic _snake_case_ or `*2*\\**2=4*` for bold *2*2=4.

        This analysis will help users develop a stronger understanding of the subject matter by reinforcing **correct concepts**, **best practices**, and **effective reasoning strategies**.
        """
    )




        
        self.misconception_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.misconception_system_prompt),
                ("human", f"Chat history: {{chat_history}}\n\n Give me a misconception report of the user using the previous chat history.")
            ]
        )

        self.misconception_chain = self.misconception_prompt | self.llm | StrOutputParser()

    async def get_misconception(self, messages):

        response = self.misconception_chain.invoke({ "datetime": datetime.now().replace(microsecond=0), "chat_history": messages})
    
        return response
