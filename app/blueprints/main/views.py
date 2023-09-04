import logging
from flask import request, jsonify
from app.blueprints.main import main
from requests.exceptions import HTTPError
from app.blueprints.main.mindsdb_login_manager import MindsDBLoginManager
from flask_jwt_extended import jwt_required, create_access_token


# create mindsdb login manager object for managing mindsdb server connections
mindsdb_login_manager = MindsDBLoginManager()


@main.route('/login', methods=['POST'])
def login():
    # if request is json, get data from json
    if request.is_json:
        request_data = request.get_json()
        login = request_data.get('login')
        password = request_data.get('password')

    # else get data from form
    else:
        login = request.form.get('login')
        password = request.form.get('password')

    # if login and password are not empty, try to connect
    if login and password:
        try:
            # connect to mindsdb server and generate access token
            mindsdb_login_manager.login(login=login, password=password)
            access_token = create_access_token(identity=login)

            return jsonify({'message': 'Login successful', 'access_token': access_token}), 200
        except HTTPError as e:
            logging.error(e)
            return jsonify({'message': 'Login unsuccessful'}), 401

    # else return error
    else:
        return jsonify({'message': 'Either the login or password has not been provided'}), 400


@main.route('/databases', methods=['PUT'])
@jwt_required()
def create_database():
    # get server object
    server = mindsdb_login_manager.get_server_connection_for_login()

    # if server object exists, create database
    if server:
        # if request is json, get data from json
        if request.is_json:
            request_data = request.get_json()
            database_name = request_data.get('database_name')
            repository = request_data.get('repository')
            api_key = request_data.get('api_key')

        # else get data from form
        else:
            database_name = request.form.get('database_name')
            repository = request.form.get('repository')
            api_key = request.form.get('api_key')

        # if database_name is not empty, create database
        if database_name and repository and api_key:
            server.create_database(database_name, 'github', {'repository': repository, 'api_key': api_key})
            return jsonify({'message': f'Database {database_name} created'}), 200

        # else return error
        else:
            return jsonify({'message': 'Either the database name, repository or API key have not been provided'}), 400

    # else return error
    else:
        return jsonify({'message': 'Access token is invalid'}), 401


@main.route('/databases', methods=['GET'])
@jwt_required()
def get_databases():
    # get server object
    server = mindsdb_login_manager.get_server_connection_for_login()

    # if server object exists, get databases
    if server:
        databases = server.list_databases()
        return jsonify({'databases': [database.name for database in databases]}), 200

    # else return error
    else:
        return jsonify({'message': 'Access token is invalid'}), 401


@main.route('/models', methods=['PUT'])
def create_model():
    pass


@main.route('/models', methods=['GET'])
@jwt_required()
def get_models():
    # get server object
    server = mindsdb_login_manager.get_server_connection_for_login()

    # if server object exists, get models
    if server:
        # get the project name from the query string
        project_name = request.args.get('project_name') if request.args.get('project_name') else 'mindsdb'

        try:
            # get the project object
            project = server.get_project(name=project_name)
        except AttributeError as e:
            logging.error(e)
            return jsonify({'message': 'Project does not exist'}), 404

        # get the models of the project
        models = project.list_models()
        return jsonify({'databases': [model.name for model in models]}), 200

    # else return error
    else:
        return jsonify({'message': 'Access token is invalid'}), 401
    

@main.route('/issues', methods=['PUT'])
def create_issue():
    pass

@main.route('/issues/description', methods=['PUT'])
def generate_issue_description():
    pass