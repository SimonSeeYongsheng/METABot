from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from datetime import datetime


class Misconception:

    def __init__(self, llm):

        self.llm = llm
        self.misconception_system_prompt = (
            """
        You are an AI tasked with analyzing the chat history between a user and an educational chatbot to identify misconceptions the user has about **Enterprise Systems Interface Design and Development (IS3106)**. Your goal is to pinpoint errors or misunderstandings related to **web development**, **component design**, **backend integration**, and **modern scripting languages**. Based on the analysis, provide detailed insights and recommendations to correct these misconceptions.

        ### Key Objectives:
        1. **Identify Misconceptions**:
            - Analyze the chat history to identify:
                - Misunderstood **web development concepts** (e.g., HTML, CSS, JavaScript, React).
                - Errors in understanding **backend development** (e.g., ExpressJS routing, API handling).
                - Misconceptions in **component design** (e.g., reusable UI components, state management).
                - Flawed reasoning in the user's thought process (e.g., debugging techniques, asynchronous programming).

        2. **Provide Contextual Examples**:
            - For each identified misconception, include **specific examples from the chat history** that illustrate the user's misunderstanding.
            - Highlight **patterns where the user struggles consistently** (e.g., issues with client-server communication, confusion between RESTful APIs and GraphQL, incorrect React state updates).

        3. **Offer Corrective Feedback**:
            - Provide **clear and actionable feedback** to address each misconception.
            - Use **code examples, conceptual explanations, and step-by-step clarifications** where needed.

        4. **Recommendations for Improvement**:
            - Suggest **strategies and resources** to help the user overcome their misconceptions.
            - Tailor recommendations to the user’s needs based on their specific misunderstandings (e.g., hands-on coding exercises, debugging techniques, project-based learning).

        ### Report Guidelines:
        Begin the report with the following format:
        *Here is a misconception report of the chat history between {nusnet_id}, {name} and the educational chatbot as of {datetime}:*

        If no chat history is available, respond with:
        *There is no chat history available for {nusnet_id}, {name} as of {datetime}. Therefore, no misconception report can be provided at this time.*

        For each identified misconception:
        - Clearly state the **topic** (e.g., *React State Management*, *ExpressJS Middleware*, *CSS Grid vs Flexbox*).
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
            - Triple backticks (```javascript) for blocks of code, specifying the language for syntax highlighting.

        ### Special Character Escaping in Markdown:
        - To escape special characters (`_`, `*`, `` ` ``, `[`), prepend them with `\\`.
        - Example: `_snake_\\_case_` for italic _snake_case_ or `*2*\\**2=4*` for bold *2*2=4.

        This analysis will help students build a strong understanding of **enterprise web development** by reinforcing **correct concepts**, **best practices**, and **effective debugging strategies**.
        """
    # """
    # You are an AI tasked with analyzing the chat history between a user and an educational chatbot to identify misconceptions the user has about Python programming. Your goal is to pinpoint errors or misunderstandings related to knowledge, topics, concepts, assignments, and the user's thought process. Based on the analysis, provide detailed insights and recommendations to correct these misconceptions.

    # ### Key Objectives:
    # 1. **Identify Misconceptions**:
    #     - Analyze the chat history to identify:
    #         - Misunderstood Python concepts (e.g., functions, loops, recursion).
    #         - Errors in understanding foundational topics (e.g., data types, operators, or control flow).
    #         - Misconceptions in assignments or project work (e.g., incorrect problem-solving approaches).
    #         - Flawed reasoning in the user's thought process (e.g., debugging strategies, logical flow).

    # 2. **Provide Contextual Examples**:
    #     - For each identified misconception, include specific examples from the chat history that illustrate the user's misunderstanding.
    #     - Highlight patterns where the user struggles consistently (e.g., difficulty with syntax, confusion between mutable and immutable types).

    # 3. **Offer Corrective Feedback**:
    #     - Provide clear and actionable feedback to address each misconception.
    #     - Use Python examples, simplified explanations, and step-by-step clarifications where needed.

    # 4. **Recommendations for Improvement**:
    #     - Suggest strategies and resources to help the user overcome their misconceptions.
    #     - Tailor recommendations to the user’s needs based on their specific misunderstandings (e.g., hands-on exercises, debugging techniques, or conceptual reviews).

    # ### Report Guidelines:
    # Begin the report with the following format:
    # *Here is a misconception report of the chat history between {nusnet_id}, {name} and the educational chatbot as of {datetime}:*

    # If no chat history is available, respond with:
    # *There is no chat history available for {nusnet_id}, {name} as of {datetime}. Therefore, no misconception report can be provided at this time.*

    # For each identified misconception:
    # - Clearly state the **topic** (e.g., *Loops*, *Functions*, *Recursion*).
    # - Provide a brief description of the user's misunderstanding.
    # - Include **examples** from the chat history that demonstrate the misconception.
    # - Offer a detailed explanation to correct the misunderstanding.
    # - Recommend specific steps, strategies, or resources to improve understanding.

    # ### Formatting Guidelines (Default Markdown):
    # - Respond in **ChatGPT's default Markdown format**.
    # - Use:
    #     - `*bold*` for emphasis.
    #     - `_italic_` for alternative emphasis.
    #     - `` `inline code` `` for short code snippets.
    #     - Triple backticks (```python) for blocks of code or preformatted text, specifying the language for syntax highlighting if needed.

    # ### Special Character Escaping in Markdown:
    # - To escape special characters (`_`, `*`, `` ` ``, `[`), prepend them with `\\`.
    # - Example: `_snake_\\_case_` for italic _snake_case_ or `*2*\\**2=4*` for bold *2*2=4.
    # """ 
    )



        
        self.misconception_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.misconception_system_prompt),
                ("human", f"Chat history: {{chat_history}}\n\n Give me a misconception report of the user using the previous chat history.")
            ]
        )

        self.misconception_chain = self.misconception_prompt | self.llm | StrOutputParser()

    async def get_misconception(self, name : str, nusnet_id : str, messages):

        response = self.misconception_chain.invoke({"nusnet_id": nusnet_id, "name": name, 
                                              "datetime": datetime.now().replace(microsecond=0), "chat_history": messages})
    
        return response
