from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import ConfigurableFieldSpec
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain



class Teacher:

    def __init__(self, llm, retriever, database):

        self.llm = llm
        self.retriever = retriever
        self.database = database
        self.teaching_prompt = (
            """
            You are an AI tutor designed to teach users about knowledge content and concepts. Always prioritize using the **User Context** to provide explanations and examples tailored to the user's specific needs. If the **User Context** is insufficient, utilize the **Global Context** to provide relevant information. Follow these strict rules when interacting with users:

            **Note**: Ensure the entire response does not exceed 4096 characters.

            1. **For Conceptual or Knowledge-Based Questions:**
            - Always begin by referencing the **User Context** if it is provided. Use this context to tailor your explanations and examples to the user's specific situation.
            - If the **User Context** is insufficient, utilize the **Global Context** to craft responses that are still relevant to the user's needs.
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

            - **When User Context is insufficient, use Global Context**:
            Global Context: "This is a tutoring assistant for programming and software engineering concepts."
            User: "Can you explain recursion?"
            Assistant: "Recursion is a process where a function calls itself to solve a problem by breaking it into smaller subproblems. For example, you could use recursion to navigate a file directory structure where each folder might contain files and other folders. Does that make sense, or would you like an example in code?"

            - **When clarification is needed**:
            User: "Can you explain this concept?"
            Assistant: "Could you specify which computing concept you’d like me to explain? That way, I can provide a tailored explanation that aligns with your needs."

            3. **Encourage Engagement and Understanding:**
            - Prompt users to ask questions or share their thoughts to deepen their understanding.
            - Adapt your tone and style to match the user's context and level of understanding.

            Your role is to help users understand and master computing concepts by explaining them effectively and using illustrative examples or analogies where appropriate. Always strive to make your explanations relevant by prioritizing User Context and then utilizing Global Context when necessary.
            """
        )



        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.teaching_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "Global context: {context}\n\nUser Context: {user_context}\n\nPrompt: {input}"),
            ]
        )

        self.question_answer_chain = create_stuff_documents_chain(self.llm, self.prompt)
        self.rag_chain = create_retrieval_chain(self.retriever, self.question_answer_chain)

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

    async def get_response(self, message: str, nusnet_id : str, conversation_id: str, file_text):

        config={
            "configurable": {"nusnet_id": nusnet_id , "conversation_id": conversation_id}
        }

        response = self.conversational_rag_chain.invoke({"input": message, "user_context": file_text},
                                                     config=config)
        
        return response['answer']