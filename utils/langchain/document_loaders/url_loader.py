from utils.langchain.document_loaders.document_loader_abc import DocumentLoaderInterface
from bs4 import BeautifulSoup
import gc
import requests


class UrlLoader(DocumentLoaderInterface):
    url = None

    def __init__(self, url):
        self.url = url

    def scrape_content(self, url):
        # Fetch the content of the URL using requests
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the content using BeautifulSoup
            soup = BeautifulSoup(response.content, 'lxml')

            # Extract only text content
            text_content = soup.get_text(separator=' ', strip=True)

            # Clean up the soup object to free memory
            soup.decompose()
            del soup
            gc.collect()

            return text_content
        else:
            raise ValueError(
                f"Failed to retrieve content. HTTP Status Code: {response.status_code}")

    def get_text(self) -> str:
        text = self.scrape_content(self.url)
        return text
