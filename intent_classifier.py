from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class Intent_Classifier:

    def __init__(self, llm):

        self.llm = llm

        self.system_prompt = """
            You are an intelligent assistant that classifies user prompts into one of three categories based on their intent:
            1. "General" - The user is engaging in casual conversation or small talk.

            2. "Guidance" - The user is seeking help, suggestions, or instructions related to an assignment or task, or requesting an explanation, elaboration, or teaching of specific content or concepts related to the course "Enterprise Systems Interface Design and Development." This includes topics such as HTML5, CSS, JavaScript, React, React Native, ExpressJS, MongoDB, API development, and web templating.

            Your task is to analyze the user prompt and respond with the category that best describes the intent of the prompt. If the prompt does not fit well into any of the categories, select the closest match.

            Only respond with the intent category. Do not provide any additional explanation unless explicitly asked.
            """

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                ("human", "{input}"),
            ]
        )

        self.intent_chain = self.prompt | self.llm | StrOutputParser()

    async def get_intent(self, message : str):

        response = self.intent_chain.invoke({"input": message})
        return response



