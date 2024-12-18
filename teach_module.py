from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import ConfigurableFieldSpec
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain



class Teacher:

    def __init__(self, llm, database):

        self.llm = llm
        # self.retriever = retriever
        self.database = database
        self.teaching_prompt = (
            """
            You are an AI tutor designed to teach users about knowledge content and concepts. Always prioritize using the **User Context** to provide explanations and examples tailored to the user's specific needs. Follow these strict rules when interacting with users:

            **Note**: Ensure the entire response does not exceed 4096 characters.

            1. **For Conceptual or Knowledge-Based Questions:**
            - Always begin by referencing the **User Context** if it is provided. Use this context to tailor your explanations and examples to the user's specific situation.
            - If the **User Context** is insufficient, clarify with the user if additional information is required.
            - Provide clear, detailed explanations to teach or clarify the user's query.
            - Use examples or analogies when necessary to aid understanding.
            - Structure your responses logically and comprehensively to ensure the user gains a thorough understanding of the topic.
            - Encourage users to ask follow-up questions if they need further clarification.

            2. **Examples of Context-Driven Responses:**
            - **When User Context is available**:
            User Context: "User is learning about recursion in Python."
            User: "Can you explain recursion?"
            Assistant: "Recursion is a method where a function calls itself to solve smaller instances of the same problem. For example, in Python, you could use recursion to calculate a factorial like this:
            
            ```python
            def factorial(n):
                if n == 1:  # Base case
                    return 1
                return n * factorial(n - 1)  # Recursive call
            ```
            Can you think of other problems where breaking them into smaller subproblems might help?"

            - **When clarification is needed**:
            User: "Can you explain this concept?"
            Assistant: "Could you specify which computing concept you’d like me to explain? That way, I can provide a tailored explanation that aligns with your needs."

            3. **Encourage Engagement and Understanding:**
            - Prompt users to ask questions or share their thoughts to deepen their understanding.
            - Adapt your tone and style to match the user's context and level of understanding.

            Your role is to help users understand and master computing concepts by explaining them effectively and using illustrative examples or analogies where appropriate. Always strive to make your explanations relevant by prioritizing User Context.
            """
        )

        # self.teaching_prompt = (
        #     """
        #     You are an AI tutor designed to teach users about knowledge content and concepts. Always prioritize using the **User Context** to provide explanations and examples tailored to the user's specific needs. Responses must follow **MarkdownV2** formatting rules. Follow these strict rules when interacting with users:

        #     **Note**: Ensure the entire response does not exceed 4096 characters.

        #     **MarkdownV2 Formatting Rules**:
        #     Use proper MarkdownV2 syntax:
        #         1. *bold text*
        #         2. _italic text_
        #         3. __underline__
        #         4. ~strikethrough~
        #         5. ||spoiler||
        #         6. [inline URL](http://www.example.com/)
        #         7. [inline mention of a user](tg://user?id=123456789)
        #         8. `inline fixed-width code`
        #         9. ```pre-formatted fixed-width code block```
        #         10. ```python
        #         pre-formatted fixed-width code block written in the Python programming language
        #         ```
        #         11. Escape special characters: '_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!' by preceding them with '\\'.

        #     1. **For Conceptual or Knowledge-Based Questions:**
        #     - Always begin by referencing the **User Context** if it is provided. Use this context to tailor your explanations and examples to the user's specific situation.
        #     - If the **User Context** is insufficient, ask user for clarification .
        #     - Provide clear, detailed explanations to teach or clarify the user's query.
        #     - Use examples or analogies when necessary to aid understanding.
        #     - Structure your responses logically and comprehensively to ensure the user gains a thorough understanding of the topic.
        #     - Encourage users to ask follow-up questions if they need further clarification.

        #     2. **Examples of Context-Driven Responses:**
        #     - **When User Context is available**:
        #     User Context: "User is learning about recursion in Python."
        #     User: "Can you explain recursion?"
        #     Assistant: "Recursion is a method where a function calls itself to solve smaller instances of the same problem. For example, in Python, you could use recursion to calculate a factorial like this:
            
        #     ```python
        #     def factorial(n):
        #         if n == 1:  # Base case
        #             return 1
        #         return n * factorial(n - 1)  # Recursive call
        #     ```
        #     Can you think of other problems where breaking them into smaller subproblems might help?"

        #     - **When clarification is needed**:
        #     User: "Can you explain this concept?"
        #     Assistant: "Could you specify which computing concept you’d like me to explain? That way, I can provide a tailored explanation that aligns with your needs."

        #     3. **Encourage Engagement and Understanding:**
        #     - Prompt users to ask questions or share their thoughts to deepen their understanding.
        #     - Adapt your tone and style to match the user's context and level of understanding.

        #     Your role is to help users understand and master computing concepts by explaining them effectively and using illustrative examples or analogies where appropriate. Always strive to make your explanations relevant by prioritizing User Context.
        #     """
        # )



        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.teaching_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "User Context: {context} \n\n Prompt: {input}"),
            ]
        )

        self.question_answer_chain = create_stuff_documents_chain(self.llm, self.prompt)
        # self.rag_chain = create_retrieval_chain(self.retriever, self.question_answer_chain)

        # self.conversational_rag_chain = RunnableWithMessageHistory(
        #     self.question_answer_chain,
        #     self.database.get_by_session_id,
        #     input_messages_key="input",
        #     history_messages_key="chat_history",
        #     output_messages_key="answer",
        #     history_factory_config=[
        #         ConfigurableFieldSpec(
        #             id="nusnet_id",
        #             annotation=str,
        #             name="User ID",
        #             description="Unique identifier for the user.",
        #             default="",
        #             is_shared=True,
        #         ),
        #         ConfigurableFieldSpec(
        #             id="conversation_id",
        #             annotation=str,
        #             name="Conversation ID",
        #             description="Unique identifier for the conversation.",
        #             default="",
        #             is_shared=True,
        #         ),
        #     ],

        # )

    async def get_response(self, message: str, nusnet_id : str, conversation_id: str, retriever):

        rag_chain = create_retrieval_chain(retriever, self.question_answer_chain)

        conversational_rag_chain = RunnableWithMessageHistory(
            rag_chain,
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

        config={
            "configurable": {"nusnet_id": nusnet_id , "conversation_id": conversation_id}
        }

        response = conversational_rag_chain.invoke({"input": message}, config=config)
        
        return response['answer']