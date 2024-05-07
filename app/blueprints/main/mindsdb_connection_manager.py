import logging
from openai import OpenAI, AuthenticationError


class MindsDBConnectionManager:
    @staticmethod
    def connect(base_url, organization, api_key):
        try:
            # connect to mindsdb inference API
            mindsdb_inference_client = OpenAI(
                base_url=base_url,
                organization=organization,
                api_key=api_key
            )

            mindsdb_inference_client.models.list()
            return mindsdb_inference_client
        except AuthenticationError as e:
            logging.error(e)
            return None
        