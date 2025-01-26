from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class Prompt_Classifier:

    def __init__(self, llm):

        self.llm = llm
        self.system_prompt = (
            """
            You are an AI designed to measure similarity between text inputs. 
            Compare the given user prompt to each prompt in the provided list and determine the most similar prompt. 
            Return only the most similar prompt from the list. If none of the prompts in the list are similar, return 'NIL' 
            with no explanation or elaboration.
            """
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                ("human", "List:{list} \n\n Prompt:{input}"),
            ]
        )

        self.intent_chain = self.prompt | self.llm | StrOutputParser()

    async def get_assignment(self, message : str, list_prompts : str):

        response = self.intent_chain.invoke({"input": message, "list": list_prompts})
        return response



