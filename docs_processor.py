import PyPDF2
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class Docs_processor:

    def __init__(self):
        pass
        
    
    def load_document(self, file_path: str, file_type: str):

        # Determine file type and process accordingly
        match file_type:

            case "pdf":
                try:
                    text = self.process_pdf(file_path)

                except Exception as e:
                    logging.error(f"Error loading PDF file: {e}")
                    raise ValueError(f"Failed to process PDF file: {file_path}")

            case _:
                try:
                    text = self.process_text_file(file_path)
                except Exception as e:
                    logging.error(f"Error loading text file: {e}")
                    raise ValueError(f"Failed to process text file: {file_path}")

        return text
    
    def process_pdf(self, file_path):

        text = ""
        with open(file_path, "rb") as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            for page in reader.pages:
                text += page.extract_text()
        return text
    
    def process_text_file(self, file_path):

        with open(file_path, "r", encoding="utf-8") as text_file:
            return text_file.read()