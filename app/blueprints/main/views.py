import ast
import logging
from flask import request, jsonify, current_app
from app.blueprints.main import main
from requests.exceptions import HTTPError
from app.blueprints.main.mindsdb_login_manager import MindsDBLoginManager
from flask_jwt_extended import jwt_required, create_access_token
from dotenv import dotenv_values
from os import environ
import logging
import jwt
import time
import requests

environ = dotenv_values(".env")

def get_jwt_github_token():
    PRIVATE_KEY = open(environ.get('PRIVATE_KEY_PATH')).read()
    APP_ID = environ.get('APP_ID')
    now = int(time.time())
    payload = {
        "iat": now,
        "exp": now + (10 * 60),
        "iss": APP_ID
    }
    token = jwt.encode(payload, PRIVATE_KEY, algorithm='RS256')
    return token

@main.route('/access_token', methods=['POST'])
def get_access_token():
    """
    This endpoint retrieves an access token using a provided code.
    """
    request_data = request.get_json() if request.is_json else request.form

    code = request_data.get('code')
    if code:
        try:
            access_token = get_access_token_from_code(code)
            logging.info("Access token retrieved successfully.")
            return jsonify({'message': 'Access token retrieved', 'access_token': access_token}), 200
        except HTTPError as e:
            logging.error(f"HTTP error occurred: {e}")
            return jsonify({'message': 'Access token could not be retrieved, please try again later.'}), 400
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return jsonify({'message': 'An error occurred, please try again later.'}), 500
    else:
        return jsonify({'message': 'Code has not been provided'}), 400

def get_access_token_from_code(code):
    """
    This function retrieves an access token using the provided code by making a POST request to GitHub.
    """
    url = 'https://github.com/login/oauth/access_token'
    headers = {'Accept': 'application/json'}
    data = {
        'client_id': environ.get('CLIENT_ID'),
        'client_secret': environ.get('CLIENT_SECRET'),
        'code': code
    }
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json().get('access_token')

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
        # if login is successful, return access token
        if mindsdb_login_manager.login(login=login, password=password):
            access_token = create_access_token(identity=login)
            return jsonify({'message': 'Login successful', 'access_token': access_token}), 200
        
        # else return error
        else:
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
            try:
                server.create_database(database_name, 'github', {'repository': repository, 'api_key': api_key})
                return jsonify({'message': f'Database {database_name} created'}), 200
            except RuntimeError as e:
                logging.error(e)
                return jsonify({'message': f'Database could not be created: {e}'}), 400

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
@jwt_required()
def create_model():
    # get server object
    server = mindsdb_login_manager.get_server_connection_for_login()

    # if server object exists, create model
    if server:
        # if request is json, get data from json
        if request.is_json:
            request_data = request.get_json()
            project_name = request_data.get('project_name') if request_data.get('project_name') else 'mindsdb'
            model_name = request_data.get('model_name')
            
        # else get data from form
        else:
            project_name = request.form.get('project_name') if request.form.get('project_name') else 'mindsdb'
            model_name = request.form.get('model_name')

        # if model_name and database_name are not empty, create model
        if model_name:
            # get the project object
            try:
                project = server.get_project(name=project_name)
            except AttributeError as e:
                logging.error(e)
                return jsonify({'message': 'Project does not exist'}), 404

            # get the OpenAI integration options from the app config
            max_tokens = current_app.config['OPENAI_MAX_TOKENS']
            prompt_template = current_app.config['OPENAI_PROMPT_TEMPLATE']

            # create model
            try:
                project.create_model(name=model_name, engine='openai', predict='generated_issue', options={'prompt_template': prompt_template, 'max_tokens': max_tokens})
                return jsonify({'message': f'Model {model_name} created'}), 200
            except RuntimeError as e:
                logging.error(e)
                return jsonify({'message': f'Model could not be created: {e}'}), 400

        # else return error
        else:
            return jsonify({'message': 'Model name has not been provided'}), 400


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
    

@main.route('/issues/description', methods=['POST'])
@jwt_required()
def generate_issue_description():
    # get server object
    server = mindsdb_login_manager.get_server_connection_for_login()

    # if server object exists, get models
    if server:
        # if request is json, get data from json
        if request.is_json:
            request_data = request.get_json()
            project_name = request_data.get('project_name') if request_data.get('project_name') else 'mindsdb'
            model_name = request_data.get('model_name')
            title = request_data.get('title')
            description = request_data.get('description')
            sections = request_data.get('sections')
            style = request_data.get('style')

        # else get data from form
        else:
            project_name = request.form.get('project_name') if request.form.get('project_name') else 'mindsdb'
            model_name = request.form.get('model_name')
            title = request.form.get('title')
            description = request.form.get('description')
            sections = request.form.get('sections')
            style = request.form.get('style')

    
        # if model_name, title, description, sections, lingo and style are not empty, generate issue description
        if model_name and title and description and sections and style:
            try:
                # get the project object
                project = server.get_project(name=project_name)
            except AttributeError as e:
                logging.error(e)
                return jsonify({'message': 'Project does not exist'}), 404
            
            try:
                # get the model object
                model = project.get_model(name=model_name)
            except AttributeError as e:
                logging.error(e)
                return jsonify({'message': 'Model does not exist'}), 404
            
            # generate issue description
            result_df = model.predict(data={'title': title, 'description': description, 'sections': sections, 'style': style})
            response = ast.literal_eval(result_df.iloc[0]['generated_issue'])

            return jsonify(response), 200
        

@main.route('/issues', methods=['PUT'])
@jwt_required()
def create_issue():
    # get server object
    server = mindsdb_login_manager.get_server_connection_for_login()

    # if server object exists, create issue
    if server:
        # if request is json, get data from json
        if request.is_json:
            database_name = request.get_json().get('database_name')
            title = request.get_json().get('title')
            description = request.get_json().get('description')

        # else get data from form
        else:
            database_name = request.form.get('database_name')
            title = request.form.get('title')
            description = request.form.get('description')

        # if database_name, title and description are not empty, create issue
        if database_name and title and description:
            # get the database object
            try:
                database = server.get_database(name=database_name)
            except AttributeError as e:
                logging.error(e)
                return jsonify({'message': 'Database does not exist'}), 404

            # create the query
            query = database.query(f'INSERT INTO issues (title, body) VALUES ("{title}", "{description}")')

            # create the issue
            try:
                query.fetch()
            except RuntimeError as e:
                logging.error(e)
                return jsonify({'message': f'Issue could not be created: {e}'}), 400

            return jsonify({'message': f'Issue "{title}" created'}), 200
        
        # else return error
        else:
            return jsonify({'message': 'Either the database name, title or description have not been provided'}), 400
        
    # else return error
    else:
        return jsonify({'message': 'Access token is invalid'}), 401