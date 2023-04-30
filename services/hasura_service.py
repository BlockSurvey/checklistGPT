import os

import requests

from config import HASURA_API_URL, HASURA_SECRET_KEY
from services.http_client import HttpClient


class HasuraService():
    http_client_object = HttpClient()

    def execute(self, operation, variables):
        # Define the headers as a dictionary
        headers = {
            "x-hasura-admin-secret": HASURA_SECRET_KEY
        }

        # Data to send in the POST request as JSON
        data = {
            "query": operation,
            "variables": variables
        }

        response = self.http_client_object.make_request(
            "POST", HASURA_API_URL, json=data, headers=headers)

        # Check the status code of the response
        if response.status_code != 200:
            # Raise an exception if the status code indicates an error
            response.raise_for_status()
        else: 
            result = response.json()
            if "errors" in result:
                print(result)

        return response.json()
