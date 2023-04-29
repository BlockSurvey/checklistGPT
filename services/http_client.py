import requests
from requests.exceptions import HTTPError


class HttpClient:
    def __init__(self):
        self.session = requests.Session()

    def make_request(self, method, url, **kwargs):
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except HTTPError as http_err:
            print(f"An HTTP error occurred: {http_err}")
            raise
        except Exception as err:
            print(f"An error occurred: {err}")
            raise
