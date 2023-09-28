import mindsdb_sdk
from dotenv import dotenv_values

environ = dotenv_values(".env")


class MindsDBIssueGenerator:
    def __init__(self, mindsdb_login: str = None, mindsdb_password: str = None, mindsdb_project: str = None, mindsdb_model: str = None) -> None:
        self.server = mindsdb_sdk.connect(
            login=mindsdb_login or environ['MINDSDB_LOGIN'], 
            password=mindsdb_password or environ['MINDSDB_PASSWORD']
        )

        self.project = self.server.get_project(name=mindsdb_project or environ['MINDSDB_PROJECT'])
        self.model = self.project.get_model(name=mindsdb_model or environ['MINDSDB_MODEL'])

    def generate_issue(self, title: str, description: str, style: str, sections: list) -> str:
        result_df = self.model.predict(
            data={
                'title': title, 
                'description': description, 
                'sections': ", ".join(sections), 
                'style': style
                }
        )

        return result_df.iloc[0]['generated_issue']

    