from utils.langchain.document_loaders.document_loader_abc import DocumentLoaderInterface
import requests
from lxml import html
import re
import gc


class UrlLoader(DocumentLoaderInterface):
    url = None

    def __init__(self, url):
        self.url = url

    def scrape_content(self, url):
        # Fetch the content of the URL using requests
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the content using lxml
            tree = html.fromstring(response.content)

            # Remove <script>, <style>, and hidden elements from the tree
            for to_remove in tree.xpath('//*[name()="script" or name()="style" or @hidden or @aria-hidden="true" or name()="input" and @type="hidden"]'):
                to_remove.getparent().remove(to_remove)

            # Extract the remaining text content of the page
            raw_text = tree.text_content().strip()

            # Clean up object and memory
            del tree
            gc.collect()

            # Replace sequences of whitespace characters with a single space
            cleaned_text = re.sub(r'\s+', ' ', raw_text)

            return cleaned_text
        else:
            raise ValueError(
                f"Failed to retrieve content. HTTP Status Code: {response.status_code}")

    def get_text(self) -> str:
        text = self.scrape_content(self.url)
        return text
