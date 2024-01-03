import requests
from enum import Enum
from time import sleep


class YandexGpt:
    def __init__(self, api_key: str, model_uri: str):
        self.api_str = api_key
        self.model_uri = model_uri

    def get_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {self.api_str}",
            "x-data-logging-enabled": "false"
        }


def retry_yandex_gpt_factory(retries=2):
    def retry_yandex_gpt(func):
        def wrapper_retry_yandex_gpt(*args, **kwargs):
            for retry in range(retries):
                res = func(*args, **kwargs)
                if (res.status_code) == 200:
                    return res.json()
                else:
                    print(f"Request failed {res.status_code}: {res.json()}, retry number: {retry + 1}")
                    if res.status_code == 429:
                        sleep(5)

        return wrapper_retry_yandex_gpt

    return retry_yandex_gpt

class Embeddings(YandexGpt):
    @retry_yandex_gpt_factory(5)
    def text_embedding(self, text: str):
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/textEmbedding"
        data = {
            "modelUri": self.model_uri,
            "text": text
        }

        return requests.post(url, json=data, headers=self.get_headers())


class MessageRole(Enum):
    SYSTEM = 'system'
    ASSISTANT = 'assistant'
    USER = 'user'


class Message:
    def __init__(self, role: MessageRole, text: str):
        self.role = role
        self.text = text


class TextGenerationAsync(YandexGpt):
    @retry_yandex_gpt_factory()
    def completion(self, messages: list[Message], stream: bool, temperature: int, max_tokens: int):
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completionAsync"
        data = {
            "modelUri": self.model_uri,
            "completionOptions": {
                "stream": stream,
                "temperature": temperature,
                "maxTokens": max_tokens
            },
            "messages": [{"role": str(msg.role.value), "text": msg.text} for msg in messages]
        }
        return requests.post(url, json=data, headers=self.get_headers())

    def get_operation(self, operation_id: str):
        url = "https://operation.api.cloud.yandex.net/operations/" + operation_id
        return requests.get(url, headers=self.get_headers()).json()

    def sync_completion(self, messages: list[Message], stream: bool, temperature: float, max_tokens: int, max_wait_secs: int):
        operation_id = self.completion(messages, stream, temperature, max_tokens)['id']

        for i in range(max_wait_secs):
            res = self.get_operation(operation_id)
            if res["done"]:
                return res
            sleep(1)
