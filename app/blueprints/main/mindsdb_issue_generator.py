from dotenv import dotenv_values
from app.blueprints.main.mindsdb_connection_manager import MindsDBConnectionManager

environ = dotenv_values(".env")


class MindsDBIssueGenerator:
    def __init__(self, base_url: str = None, organization: str = None, api_key: str = None, model: str = None) -> None:
        self.mindsdb_inference_client = MindsDBConnectionManager.connect(
            base_url=base_url or environ.get('MDB_INFERENCE_API_BASE_URL'),
            organization=organization or environ.get('MDB_INFERENCE_API_ORGANIZATION'),
            api_key=api_key or environ.get('MDB_INFERENCE_API_KEY')
        )
        self.model = model or environ.get('MDB_INFERENCE_API_MODEL')

    def generate_issue(self, system_prompt: str, title: str, description: str, style: str, sections: list) -> str:
        respone = self.mindsdb_inference_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt.format(sections=", ".join(sections), style=style)
                },
                {"role": "user", "content": "Title: '{title}', Description: '{description}'".format(title=title, description=description)}
            ],
            model=self.model
        )

        return respone.choices[0].message.content

    