from waitress import serve
from app import create_app
from config import DevelopmentConfig, ProductionConfig, TestingConfig
from flask_cors import CORS



# pass the config you want to use here, defaults to DevelopmentConfig
app = create_app()

# enable CORS for all routes
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=4000)