from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class Assignment_Classifier:

    def __init__(self, llm):

        self.llm = llm
        self.system_prompt = """
        You are an AI assistant specialized in formatting and classifying assignment names. 
        Your task is to process user inputs and return a clean, well-formatted version of the assignment name. 
        Additionally, check if the formatted input matches any of the assignments in the provided List of Unique Assignments. 
        If a match is found, return the assignment from the list that most closely matches the user input; 
        otherwise, return only the formatted input.

        Follow these rules:
        1. Convert all text to lowercase.
        2. Correct any spelling or typographical errors.
        3. Remove any leading zeros from numbers (e.g., '05' becomes '5').
        4. Preserve the structure and meaning of the input while ensuring consistency in formatting.
        5. Ensure the matching process allows for slight variations in formatting, spelling, or numbering to identify the closest match.
        6. If no sufficiently close match is found, return the formatted input without any additional context or explanation.

        Example Process:
        - Input: 'List of unique assignments: ["lecture 3", "tutorial 5", "mission 10", "sidequest 5.2", "recitation 4"] \n\n Input: "Lecture 03"' 
          → Output: 'lecture 3'
        - Input: 'List of unique assignments: ["lecture 3", "tutorial 5", "mission 10", "sidequest 5.2", "recitation 4"] \n\n Input: "Mission 10"' 
          → Output: 'mission 10'
        - Input: 'List of unique assignments: ["lecture 3", "tutorial 5", "mission 10", "sidequest 5.2", "recitation 4"] \n\n Input: "Extra Practice on Basic Python Concepts"' 
          → Output: 'extra practice on basic python concepts'
        - Input: 'List of unique assignments: ["lecture 3", "tutorial 5", "mission 10", "sidequest 5.2", "recitation 4"] \n\n Input: "Lecture 02"' 
          → Output: 'lecture 2'

        Ensure that the output is clean, consistent, and error-free. 
        Do not change the meaning of the input and do not introduce any additional information.
        """



        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                ("human", "List of unique assignments: {list_assignments} \n\n Input: {input}"),
            ]
        )

        self.intent_chain = self.prompt | self.llm | StrOutputParser()

    async def get_assignment(self, message : str, list_assignments : str):

        response = self.intent_chain.invoke({"input": message, "list_assignments" : list_assignments})
        return response



