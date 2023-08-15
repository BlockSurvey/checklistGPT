from langchain import OpenAI
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from utils.langchain.document_loaders.document_loader_abc import DocumentLoaderInterface

from PyPDF2 import PdfReader


class PdfLoader(DocumentLoaderInterface):
    uploaded_file = None

    def __init__(self, file):
        self.uploaded_file = file

    def extract_text_from_pdf(self):
        pdf_reader = PdfReader(self.uploaded_file)
        texts = [page.extract_text() for page in pdf_reader.pages]
        return ''.join(texts)

    def get_text(self):
        extracted_text = self.extract_text_from_pdf()
        return extracted_text
