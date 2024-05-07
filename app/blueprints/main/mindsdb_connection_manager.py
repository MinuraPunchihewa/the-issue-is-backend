import logging
from openai import OpenAI, AuthenticationError


class MindsDBConnectionManager:
    @staticmethod
    def connect(base_url: str, organization: str, api_key: str) -> OpenAI:
        try:
            # connect to mindsdb inference API
            mindsdb_inference_client = OpenAI(
                base_url=base_url,
                organization=organization,
                api_key=api_key
            )

            # list models to check if credentials are valid
            mindsdb_inference_client.models.list()
            return mindsdb_inference_client
        except AuthenticationError as e:
            logging.error(e)
            return None
        