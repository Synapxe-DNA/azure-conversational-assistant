import uuid

import requests
from config import (
    CONFIG_TRANSLATOR_SERVICE_API_KEY,
    CONFIG_TRANSLATOR_SERVICE_ENDPOINT,
    CONFIG_TRANSLATOR_SERVICE_LOCATION,
)
from quart import current_app


class Translator:

    def __init__(self):
        self.key = current_app.config[CONFIG_TRANSLATOR_SERVICE_API_KEY]
        self.location = current_app.config[CONFIG_TRANSLATOR_SERVICE_LOCATION]
        self.endpoint = current_app.config[CONFIG_TRANSLATOR_SERVICE_ENDPOINT]
        self.path = "/translate"
        self.url = self.endpoint + self.path
        self.headers = {
            "Ocp-Apim-Subscription-Key": self.key,
            "Ocp-Apim-Subscription-Region": self.location,
            "Content-type": "application/json",
            "X-ClientTraceId": str(uuid.uuid4()),
        }

    def translate(self, text, lang):
        params = {"api-version": "3.0", "from": "en", "to": lang}
        body = [{"text": text}]
        request = requests.post(self.url, params=params, headers=self.headers, json=body)
        response = request.json()
        print(response)
        return response[0]["translations"][0]["text"]
