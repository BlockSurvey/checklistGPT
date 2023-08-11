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

    def convert_pages_to_text(self, pages):
        text = ""
        for page in pages:
            text += page.page_content
        return text

    def generate_embeddings_for_text(self):
        # Load the file
        loader = PyPDFLoader('./assets/Sales Follow Up Checklist.pdf')
        pages = loader.load()

        # pages to text
        text = self.convert_pages_to_text(pages)
        text = text.replace('\t', ' ')

        # Text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", "\t"], chunk_size=10000, chunk_overlap=3000)
        splitted_docs = text_splitter.create_documents([text])

        embeddings_model = OpenAIEmbeddings()

        embeddings = embeddings_model.embed_documents(
            [doc.page_content for doc in splitted_docs])

        return {
            "splitted_docs": splitted_docs,
            "embeddings": embeddings
        }
