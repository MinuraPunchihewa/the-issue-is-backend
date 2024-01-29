import os
# uncomment the lines below if you want to use .env file
from dotenv import dotenv_values

environ = dotenv_values(".env")

# create the base config
class Config(object):
    SECRET_KEY = environ.get('SECRET_KEY')
    OPENAI_PROMPT_TEMPLATE = """"""
    OPENAI_MAX_TOKENS = 1024
    SECTION_NAMES = {}


# create the development config
class DevelopmentConfig(Config):
    DEBUG = True
    OPENAI_PROMPT_TEMPLATE = """
    You are a GitHub user and you want to create a new issue. You will be given a title and a description.
    You are required to elaborate on the issue by providing the following sections: {{sections}}.

    In describing the issue, you should use the following style: {{style}}.

    You should provide clear instructions, carefully craft descriptions, and use structured formatting.

    Title: '{{title}}'
    Description: '{{description}}'

    Your response should be a string formatted with markdown syntax. Do not include any other information in your response.
    """
    ISSUE_SECTION_NAMES = {
        'has_steps',
        'has_impact',
        'has_location',
        'has_expected',
        'has_culprit'
    }
    
    ISSUE_SECTION_NAME_MAPPING = {
        'has_steps': "Steps to reproduce", 
        'has_impact': "Impact", 
        'has_location': "Location", 
        'has_expected': "Expected behaviour",
        'has_culprit': "Suspected culprit"
    }

    LINGO_REQUIRED_FIELDS = {
        'name',
        'style',
        'user_id',
        'sections'
    }


# create the production config
class ProductionConfig(Config):
    OPENAI_PROMPT_TEMPLATE = """"""


# create the testing config
class TestingConfig(Config):
    OPENAI_PROMPT_TEMPLATE = """"""