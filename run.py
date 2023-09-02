from app import create_app
from config import DevelopmentConfig, ProductionConfig, TestingConfig

app = create_app()


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, use_reloader=False)