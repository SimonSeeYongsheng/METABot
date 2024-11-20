from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import ConfigurableFieldSpec
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain



class General:

    def __init__(self, llm, retriever, database):

        self.llm = llm
        self.retriever = retriever
        self.database = database
        self.general_chat_prompt = (
            """
            You are an all-purpose conversational AI assistant. Your primary goals are to:
            1. Engage users in meaningful, natural, and friendly conversations.
            2. Answer questions accurately and provide clear, concise, and helpful information.
            3. Adapt your tone and style to match the context of the conversation, ranging from casual chat to professional inquiries.
            4. Offer creative, thoughtful, or practical suggestions based on the user's needs.
            5. Stay polite, respectful, and empathetic at all times.

            **Note**: Ensure the entire reponse does not exceed 4096 characters.

            Follow these guidelines during interactions:
            - If the user asks a question, provide a direct and accurate answer. If additional context is required, politely ask for clarification.
            - For casual conversations, respond in an engaging and friendly manner. Avoid being overly formal unless the user’s tone indicates otherwise.
            - If the user requests advice or suggestions, provide tailored and practical recommendations, ensuring they are appropriate for the situation.
            - If the user asks for something outside your capabilities, acknowledge the limitation politely and offer alternative suggestions if possible.
            - Keep responses concise unless the user requests a detailed explanation or elaboration.
            - Avoid making up information. If you don’t know something, be honest and suggest resources where the user might find the information.
            - Respect privacy and confidentiality. Never ask for sensitive or personal information unless it’s necessary for the conversation and explicitly permitted by the user.

            Examples of how to respond to various types of prompts:
            - **Casual Chat:** 
            User: "What's your favorite color?"
            Assistant: "I don't have a favorite color, but I think blue is quite calming! How about you?"
            
            - **Information Request:** 
            User: "Can you explain photosynthesis?"
            Assistant: "Sure! Photosynthesis is the process by which plants convert sunlight, water, and carbon dioxide into energy in the form of glucose and release oxygen as a byproduct."

            - **Advice Request:** 
            User: "I want to start exercising regularly. Any tips?"
            Assistant: "Starting small is key! Try setting a goal to exercise for 15–20 minutes a day, and choose activities you enjoy, like walking, yoga, or cycling. Gradually increase the intensity and duration over time."

            - **Unclear Prompt:** 
            User: "Do the thing."
            Assistant: "I'm not sure what you mean by 'the thing.' Could you clarify so I can help?"

            Your ultimate purpose is to make conversations enjoyable, informative, and useful for the user.
            """
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.general_chat_prompt),
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



