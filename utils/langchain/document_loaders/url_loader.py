from utils.langchain.document_loaders.document_loader_abc import DocumentLoaderInterface
import requests
from lxml import html
import re
import gc
import time

class UrlLoader(DocumentLoaderInterface):
    url = None

    def __init__(self, url: str, max_retries: int = 5, backoff_factor: float = 1.0):
        self.url = url
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Checklist/1.0; +https://checklist.gg/)"
        }

    def scrape_content(self) -> str:
        for attempt in range(self.max_retries):
            resp = requests.get(self.url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                break
            if resp.status_code == 429 and attempt < self.max_retries - 1:
                # exponential back‑off
                time.sleep(self.backoff_factor * (2 ** attempt))
                continue
            raise ValueError(f"Failed to retrieve {self.url}: HTTP {resp.status_code}")

        tree = html.fromstring(resp.content)
        # strip scripts, styles, hidden inputs, etc.
        for node in tree.xpath(
            '//*[name()="script" or name()="style" or @hidden'
            ' or @aria-hidden="true" or (name()="input" and @type="hidden")]'
        ):
            node.getparent().remove(node)

        raw = tree.text_content()
        del tree
        gc.collect()

        # collapse whitespace
        return re.sub(r"\s+", " ", raw).strip()

    def get_text(self) -> str:
        return self.scrape_content()
