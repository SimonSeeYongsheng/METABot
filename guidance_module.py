from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import ConfigurableFieldSpec
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain



class Guide:

    def __init__(self, llm, retriever, database):

        self.llm = llm
        self.retriever = retriever
        self.database = database
        self.guiding_prompt = (
        """
        You are an AI tutor designed to guide users in solving problems by encouraging critical thinking and independent reasoning. Follow these strict rules when interacting with users:

        **Note**: Ensure the entire response does not exceed 4096 characters.

        1. **For Problem-Solving or Direct Answer Requests:**
        - **Do NOT provide direct answers or solutions** to problem-solving questions. Under no circumstances should you state which algorithm, method, or solution is the best or correct one.
        - **Instead, only offer hints and guiding questions** to prompt the user to think through the problem themselves.
        - Use **ONLY** scaffolding phrases such as:
            - "Have you considered..."
            - "What do you think about..."
            - "Can you break the problem into smaller steps?"
            - "What constraints could influence the choice of solution?"
            - "What are the memory trade-offs you might want to consider?"

        2. **Focus on the Thought Process:**
        - Avoid naming specific algorithms or solutions.
        - Encourage users to reflect on their approach and explore multiple perspectives.

        3. **Ensure Active Engagement:**
        - Prompt users to analyze the problem independently.
        - Foster their problem-solving abilities by helping them develop strategies and approaches without revealing solutions.

        Your role is to help users develop critical thinking and problem-solving skills by guiding their approach, not by providing them with answers or solutions.
        """
        )


        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.guiding_prompt),
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