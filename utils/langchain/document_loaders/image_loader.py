from utils.langchain.document_loaders.document_loader_abc import DocumentLoaderInterface
from PIL import Image
import pytesseract


class ImageLoader(DocumentLoaderInterface):
    uploaded_file = None

    def __init__(self, file):
        self.uploaded_file = file

    def extract_text_from_image(self):
        # Use PIL to open the image
        image = Image.open(self.uploaded_file)

        # Use Tesseract to do OCR on the image
        text = pytesseract.image_to_string(image)
        print(text)
        return text

    def get_text(self):
        extracted_text = self.extract_text_from_image()
        return extracted_text
