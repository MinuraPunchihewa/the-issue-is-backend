import logging
from requests.exceptions import HTTPError
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, create_access_token

from app.blueprints.main import main
from app.blueprints.main.github_token_manager import GitHubTokenManager
from app.blueprints.main.mindsdb_login_manager import MindsDBLoginManager
from app.blueprints.main.mindsdb_issue_generator import MindsDBIssueGenerator
from app.blueprints.main.postgres_database_manager import PostgresDatabaseManager
from app.blueprints.main.email_sender_manager import EmailSenderManager

# create mindsdb login manager object for managing mindsdb server connections
mindsdb_login_manager = MindsDBLoginManager()

# create postgres database manager object for executing database operations
postgres_database_manager = PostgresDatabaseManager()

# create github token manager object for managing github tokens and user information
github_token_manager = GitHubTokenManager()

# create email sender manager object for sending emails
email_manager = EmailSenderManager()

@main.route('/access_token', methods=['POST'])
def get_access_token():
    """
    This endpoint retrieves an access token using a provided code.
    """
    request_data = request.get_json() if request.is_json else request.form
    code = request_data.get('code')
    
    if code:
        try:
            access_token, expires_in, refresh_token, refresh_token_expires_in = github_token_manager.get_access_token_from_code(code)
            logging.info("Access token retrieved successfully.")
            
            user_data = github_token_manager.get_user_information_from_token(access_token)
            logging.info("User data retrieved successfully.")

            username = user_data.get('login')
            github_user_id = user_data.get('id')

            postgres_database_manager.upsert_user_by_github_user_id(username, github_user_id, access_token, expires_in, refresh_token, refresh_token_expires_in)
            logging.info("Stored user data in database successfully")
            
            return jsonify({'message': 'Access token retrieved', 'access_token': access_token, 'username': username, 'user_id': github_user_id}), 200
        except HTTPError as e:
            logging.error(f"HTTP error occurred: {e}")
            return jsonify({'message': 'Access token could not be retrieved, please try again later.'}), 400
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return jsonify({'message': 'An error occurred, please try again later.'}), 500
    else:
        return jsonify({'message': 'Code has not been provided'}), 400
    

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


REQUIRED_FIELDS = {'name', 'style', 'user_id', 'sections'}
SECTION_NAMES = {'has_steps', 'has_impact', 'has_location', 'has_expected', 'has_culprit'}

@main.route('/create_lingo', methods=['POST'])
def create_lingo():
    request_data = request.get_json()

    if not request_data:
        return jsonify({'error': 'No input data provided'}), 400

    missing_fields = REQUIRED_FIELDS - request_data.keys()
    if missing_fields:
        return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

    name = request_data['name']
    style = request_data['style']
    github_user_id = request_data['user_id']
    sections = set(request_data['sections'])

    section_flags = {section_name: section_name in sections for section_name in SECTION_NAMES}

    try:
        user_data = postgres_database_manager.select_user_by_github_user_id(github_user_id)
        if not user_data:
            return jsonify({'error': 'User does not exist.'}), 400

        user_id = user_data['user_id']
        postgres_database_manager.insert_lingo_by_github_user_id(
            user_id, name, style, **section_flags
        )
        return jsonify({'message': f'Lingo {name} created'}), 200

    except Exception as e:
        logging.error(e)
        return jsonify({'error': f'Lingo could not be created: {str(e)}'}), 400

@main.route('/lingo', methods=['POST'])
def get_lingos():
    request_data = request.get_json()

    if not request_data:
        return jsonify({'error': 'No input data provided'}), 400
    
    github_user_id = request_data['user_id']

    try:
        lingos = postgres_database_manager.select_lingo_by_github_user_id(github_user_id)
        ## make a list of the lingos 
        # [{'name': 'loling'}, {'name': 'lollingo'}, {'name': 'lol'}] -> ['loling', 'lollingo', 'lol']
        lingos = [lingo['name'] for lingo in lingos]
        return jsonify({'lingos': lingos}), 200
    
    except Exception as e:
        logging.error(e)
        return jsonify({'error': f'Lingos could not be retrieved: {str(e)}'}), 400
    
@main.route('/repos', methods=['POST'])
def get_repos():
    jwt = github_token_manager.jws_for_github_app()
    request_data = request.get_json()
    github_user_id = request_data['user_id']
    user = postgres_database_manager.select_user_by_github_user_id(github_user_id)
    print(user)
    token = user['access_token']
    

    if not request_data:
        return jsonify({'error': 'No input data provided'}), 400
    
    try:
        repos = github_token_manager.get_installation_repos(jwt, token)
        return jsonify({'repos': repos}), 200
    
    except Exception as e:
        logging.error(e)
        return jsonify({'error': f'Repos could not be retrieved: {str(e)}'}), 400



@main.route('/create_issue', methods=['POST'])
def create_issue1():
    request_data = request.get_json()

    if not request_data:
        return jsonify({'error': 'No input data provided'}), 400
    
    github_user_id = request_data['user_id']
    repository = request_data['repository']
    owner = request_data['owner']
    title = request_data['issueTitle']
    body = request_data['issuePreview']

    try:
        user = postgres_database_manager.select_user_by_github_user_id(github_user_id)
        token = user['access_token']
        html_url = github_token_manager.create_issue(token, repository, owner, title, body)

        user_id = user['user_id']
        postgres_database_manager.insert_issue(user_id, repository, owner, html_url)

        return jsonify({'message': 'Issue created', 'html_url': html_url}), 200
    
    except Exception as e:
        logging.error(e)
        return jsonify({'error': f'Issue could not be created: {str(e)}'}), 400
    
@main.route('/generate_issue', methods=['POST'])
def generate_issue():

    request_data = request.get_json()

    if not request_data:
        return jsonify({'error': 'No input data provided'}), 400

    # TODO: do we need the repository and owner? How will they be used? For the future we could use them as more context.
    # repository = request_data['repository']
    # owner = request_data['owner']
    title = request_data['issueTitle']
    description = request_data['issueDescription']
    lingo = request_data['lingo']
    user_id = request_data['user_id']

    try:
        lingo_data = postgres_database_manager.select_lingo(user_id, lingo)
        sections = []
        for key, value in lingo_data.items():
            if key.startswith('has_') and value:
                sections.append(current_app.config['SECTION_NAMES'][key])

        mindsdb_issue_generator = MindsDBIssueGenerator()
        issue_preview = mindsdb_issue_generator.generate_issue(title, description, lingo_data['style'], sections)

        return jsonify({'issuePreview': issue_preview}), 200

    except Exception as e:
        logging.error(e)
        return jsonify({'error': f'Issue could not be created: {str(e)}'}), 400


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
        return jsonify({'models': [model.name for model in models]}), 200

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
            response = result_df.iloc[0]['generated_issue']

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


## Send contact us email endpoint. it recieves the email and the message from the contact us form and sends it to the  team
@main.route('/contact_us', methods=['POST'])
def contact_us():
    request_data = request.get_json()

    if not request_data:
        return jsonify({'error': 'No input data provided'}), 400

    email = request_data.get('email', ' ')
    body = request_data.get('body', ' ')

    try:
        success = email_manager.send_email(
            "New Message from Contact Form:" + " " + email,  # subject
            'theissueai@gmail.com',  # sender
            ['theissueai@gmail.com'],  # recipients
            body + " " + email,  # text body
            body + " " + email  # html body
        )
        if success:
            return jsonify({'message': 'Email sent successfully'}), 200
        else:
            raise Exception("Failed to send email via EmailSenderManager")

    except Exception as e:
        logging.error(e)
        return jsonify({'error': f'Email could not be sent: {str(e)}'}), 400
