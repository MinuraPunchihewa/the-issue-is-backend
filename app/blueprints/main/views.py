import logging
from requests.exceptions import HTTPError
from flask import request, jsonify, current_app

from app.blueprints.main import main
from app.blueprints.main.github_token_manager import GitHubTokenManager
from app.blueprints.main.mindsdb_issue_generator import MindsDBIssueGenerator
from app.blueprints.main.postgres_database_manager import PostgresDatabaseManager
from app.blueprints.main.email_sender_manager import EmailSenderManager

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


@main.route('/create_lingo', methods=['POST'])
def create_lingo():
    request_data = request.get_json()

    if not request_data:
        return jsonify({'error': 'No input data provided'}), 400

    missing_fields = current_app.config['LINGO_REQUIRED_FIELDS'] - request_data.keys()
    if missing_fields:
        return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

    name = request_data['name']
    style = request_data['style']
    github_user_id = request_data['user_id']
    sections = set(request_data['sections'])

    section_flags = {section_name: section_name in sections for section_name in current_app.config['ISSUE_SECTION_NAMES']}

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
def create_issue():
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
        user_id = user['user_id']
    except Exception as e:
        logging.error(e)
        return jsonify({'error': f'User does not exist: {str(e)}'}), 400

    try:
        token = user['access_token']
        html_url = github_token_manager.create_issue(token, repository, owner, title, body)

        postgres_database_manager.insert_issue(user_id, repository, owner, html_url)
        postgres_database_manager.update_user_stats(user_id, True, True)

        return jsonify({'message': 'Issue created', 'html_url': html_url}), 200
    
    except Exception as e:
        logging.error(e)
        postgres_database_manager.update_user_stats(user_id, True, False)
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
    github_user_id = request_data['user_id']

    try:
        user = postgres_database_manager.select_user_by_github_user_id(github_user_id)
        user_id = user['user_id']
    except Exception as e:
        logging.error(e)
        return jsonify({'error': f'User does not exist: {str(e)}'}), 400

    try:
        lingo_data = postgres_database_manager.select_lingo(github_user_id, lingo)
        sections = []
        for key, value in lingo_data.items():
            if key.startswith('has_') and value:
                sections.append(current_app.config['ISSUE_SECTION_NAME_MAPPING'][key])

        system_prompt = current_app.config['SYSTEM_PROMPT'] 

        mindsdb_issue_generator = MindsDBIssueGenerator()
        issue_preview = mindsdb_issue_generator.generate_issue(system_prompt, title, description, lingo_data['style'], sections)

        postgres_database_manager.update_user_stats(user_id, False, True)

        return jsonify({'issuePreview': issue_preview}), 200

    except Exception as e:
        logging.error(e)
        postgres_database_manager.update_user_stats(user_id, False, False)
        return jsonify({'error': f'Issue could not be created: {str(e)}'}), 400


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
