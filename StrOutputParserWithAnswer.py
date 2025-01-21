from langchain_core.output_parsers import StrOutputParser


class StrOutputParserWithAnswer(StrOutputParser):
    def parse(self, output: str) -> dict:
        return {"answer": output}  # Wrap output in a dictionary with the 'answer' key