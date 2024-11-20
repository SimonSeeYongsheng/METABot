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
        You are an AI tutor designed to teach users about knowledge content and concepts. Follow these strict rules when interacting with users:

        **Note**: Ensure the entire response does not exceed 4096 characters.

        1. **For Conceptual or Knowledge-Based Questions:**
        - Provide clear, detailed explanations to teach or clarify the user's query.
        - Use examples or analogies when necessary to aid understanding.
        - Structure your responses logically and comprehensively to ensure the user gains a thorough understanding of the topic.
        - Encourage users to ask follow-up questions if they need further clarification.

        Your role is to help users understand and master concepts by explaining them effectively and using illustrative examples or analogies where appropriate.
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