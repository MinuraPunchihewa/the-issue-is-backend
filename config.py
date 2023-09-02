import os
from dotenv import load_dotenv

load_dotenv()


# create the base config
class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY')


# create the development config
class DevelopmentConfig(Config):
    DEBUG = True


# create the production config
class ProductionConfig(Config):
    pass


# create the testing config
class TestingConfig(Config):
    pass