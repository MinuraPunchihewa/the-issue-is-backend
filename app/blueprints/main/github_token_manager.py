import logging
import requests
from dotenv import dotenv_values
from requests.exceptions import HTTPError

environ = dotenv_values(".env")


class GitHubTokenManager:
    def __init__(self, client_id=None, client_secret=None) -> None:
        self.client_id = client_id or environ['CLIENT_ID']
        self.client_secret = client_secret or environ['CLIENT_SECRET']

    def get_access_token_from_code(self, code :str) -> tuple:
        try:
            url = 'https://github.com/login/oauth/access_token'
            headers = {'Accept': 'application/json'}
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code
            }
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()

            response_data = response.json()
            access_token = response_data.get('access_token')
            expires_in = response_data.get('expires_in')
            refresh_token = response_data.get('refresh_token')
            refresh_token_expires_in = response_data.get('refresh_token_expires_in')
        except HTTPError as e:
            logging.error(f"HTTP error occurred: {e}")
            raise e
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            raise e
        else:
            return access_token, expires_in, refresh_token, refresh_token_expires_in
        
    def get_user_information_from_token (self, access_token: str) -> dict:
        url = 'https://api.github.com/user'
        headers = {'Authorization': f'bearer {access_token}'}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            user_data = response.json()
            login = user_data.get('login')
            id = user_data.get('id')
        except HTTPError as e:
            logging.error(f"HTTP error occurred: {e}")
            raise e
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            raise e
        else:
            return {'login': login, 'id': id}