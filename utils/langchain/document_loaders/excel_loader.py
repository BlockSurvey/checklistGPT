from utils.langchain.document_loaders.document_loader_abc import DocumentLoaderInterface
import pandas as pd


class ExcelLoader(DocumentLoaderInterface):
    uploaded_file = None

    def __init__(self, file):
        self.uploaded_file = file

    def get_file_content(self):
        # Read the Excel content using pandas
        data_frame = pd.read_excel(self.uploaded_file, engine='openpyxl')

        # Convert each row of the DataFrame to a readable string
        return ". ".join(
            [". ".join(row.dropna().astype(str).tolist()) for _, row in data_frame.iterrows()])

    def get_text(self) -> str:
        return self.get_file_content()
