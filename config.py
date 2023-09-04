import os
from dotenv import load_dotenv

load_dotenv()


# create the base config
class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    PROMPT_TEMPLATE = """"""


# create the development config
class DevelopmentConfig(Config):
    DEBUG = True
    PROMPT_TEMPLATE = """
    You are a GitHub user and you want to create a new issue. You will be given a title and a description.
    You are required to elaborate on the issue by providing the following sections: {{sections}}.

    In describing the issue, you should use the lingo: {{lingo}} and the style: {{style}}.

    You should provide clear instructions, carefully craft descriptions, and use structured formatting.

    Title: '{{title}}'
    Description: '{{description}}'.
    """


# create the production config
class ProductionConfig(Config):
    PROMPT_TEMPLATE = """"""


# create the testing config
class TestingConfig(Config):
    PROMPT_TEMPLATE = """"""