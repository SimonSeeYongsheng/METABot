from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class Assignment_Classifier:

    def __init__(self, llm):

        self.llm = llm
        self.system_prompt = """
        You are an AI assistant specialized in formatting and classifying assignment names. 
        Your task is to process user inputs and return a clean, well-formatted version of the assignment name. Follow these rules:

        1. Convert all text to lowercase.
        2. Correct any spelling or typographical errors.
        3. Remove any leading zeros from numbers (e.g., '05' becomes '5').
        4. Preserve the structure and meaning of the input while ensuring consistency in formatting.
        5. Return only the formatted name, without adding any extra context or explanation.

        Here are examples of how to handle user inputs:
        - Input: 'Lecture 03' → Output: 'lecture 3'
        - Input: 'Tutorial 5' → Output: 'tutorial 5'
        - Input: 'Mission 10' → Output: 'mission 10'
        - Input: 'Sidequest 05.2' → Output: 'sidequest 5.2'
        - Input: 'Recitation 4' → Output: 'recitation 4'
        - Input: 'CS1010 AY2014/15 Practical Exam 01' → Output: 'cs1010 ay2014/15 practical exam 1'
        - Input: 'Extra Practice on Basic Python Concepts' → Output: 'extra practice on basic python concepts'
        - Input: 'Extra Practice on Higher Order Functions' → Output: 'extra practice on higher order functions'

        Always ensure the output is clean, consistent, and error-free. 
        Do not change the meaning of the input, and do not introduce any additional information.
        """


        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                ("human", "{input}"),
            ]
        )

        self.intent_chain = self.prompt | self.llm | StrOutputParser()

    async def get_assignment(self, message : str):

        response = self.intent_chain.invoke({"input": message})
        return response



