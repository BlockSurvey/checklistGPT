from utils.langchain.document_loaders.document_loader_abc import DocumentLoaderInterface
import pandas as pd


class CsvLoader(DocumentLoaderInterface):
    uploaded_file = None

    def __init__(self, file):
        self.uploaded_file = file

    def get_file_content(self):
        data_frame = pd.read_csv(self.uploaded_file)
        content = ". ".join([". ".join(row.dropna().astype(str).tolist())
                            for _, row in data_frame.iterrows()])
        return content

    def get_text(self) -> str:
        return self.get_file_content()
