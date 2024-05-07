import os
# uncomment the lines below if you want to use .env file
from dotenv import dotenv_values

environ = dotenv_values(".env")

# create the base config
class Config(object):
    SECRET_KEY = environ.get('SECRET_KEY')
    SYSTEM_PROMPT = """"""
    MAX_TOKENS = 1024
    SECTION_NAMES = {}


# create the development config
class DevelopmentConfig(Config):
    DEBUG = True
    SYSTEM_PROMPT = """
    You are a GitHub user preparing to submit a new issue. You will be provided with a title and a detailed description of the issue. Your task is to expand on this information by including only the specific sections: {sections}.

    Style Requirements:
    You should adhere to the style specified in {style}. Ensure your response is well-organized, clearly articulated, and formatted appropriately for readability.

    Formatting Instructions:
    Structure your response using Markdown syntax, utilizing headers, lists, and tables where appropriate.
    Any segments of the text resembling code should be enclosed in code blocks.
    Portions that appear to be error logs or console outputs should also be formatted as code blocks.

    Additional Guidelines:
    Provide clear, actionable instructions and detailed descriptions within each required section.
    Do not include any information outside the scope of the given issue.
    Emphasize structured formatting to enhance the presentation and clarity of the issue.
    Do not include the title in the output.
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
    SYSTEM_PROMPT = """"""


# create the testing config
class TestingConfig(Config):
    SYSTEM_PROMPT = """"""