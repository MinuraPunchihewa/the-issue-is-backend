from waitress import serve
from app import create_app
from config import DevelopmentConfig, ProductionConfig, TestingConfig

# pass the config you want to use here, defaults to DevelopmentConfig
app = create_app()


if __name__ == '__main__':
    serve(app, host='0.0.0.0')