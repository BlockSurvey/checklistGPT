from utils.langchain.document_loaders.document_loader_abc import DocumentLoaderInterface
from docx import Document

class DocxLoader(DocumentLoaderInterface):
    uploaded_file = None

    def __init__(self, file):
        self.uploaded_file = file
        
    def extract_text_from_docx(self):
        document = Document(self.uploaded_file)
        full_text = []
        for paragraph in document.paragraphs:
            full_text.append(paragraph.text)
        return '\n'.join(full_text)

    def get_text(self) -> str:
        return self.extract_text_from_docx()