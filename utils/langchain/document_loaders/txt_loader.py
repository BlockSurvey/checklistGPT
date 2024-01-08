from utils.langchain.document_loaders.document_loader_abc import DocumentLoaderInterface


class TxtLoader(DocumentLoaderInterface):
    uploaded_file = None

    def __init__(self, file):
        self.uploaded_file = file

    def read_text_file(self):
        text = self.uploaded_file.read().decode('utf-8')

        # Reset the pointer to the beginning of the file
        self.uploaded_file.seek(0)

        return text

    def get_text(self) -> str:
        return self.read_text_file()
