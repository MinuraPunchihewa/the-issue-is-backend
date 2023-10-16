import logging
import requests
from dotenv import dotenv_values
import jwt
import time
from requests.exceptions import HTTPError

environ = dotenv_values(".env")


class GitHubTokenManager:
    def __init__(self, client_id=None, client_secret=None, app_id=None, private_key=None) -> None:
        self.client_id = client_id or environ['CLIENT_ID']
        self.client_secret = client_secret or environ['CLIENT_SECRET']
        self.app_id = app_id or environ['APP_ID']
        self.private_key = private_key or environ['PRIVATE_KEY_PATH']

    def jws_for_github_app(self) -> str:
        """
        Creates a JWS for the GitHub App.
        """
        app_id = self.app_id
        payload = {
            # issued at time
            'iat': int(time.time()),
            # JWT expiration time (10 minute maximum)
            'exp': int(time.time()) + (10 * 60),
            # GitHub App's identifier
            'iss': app_id
        }

        with open(self.private_key, 'rb') as pem_file:
            signing_key = pem_file.read()

        encoded_jwt = jwt.encode(payload, signing_key, algorithm='RS256')

        # Sign with the app's private key
        return encoded_jwt


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
        
    # def get_repos(self, access_token: str, username: str) -> list:
    #     url = f"https://api.github.com/users/{username}/repos?per_page=40&type=all"
    #     # url = f"https://api.github.com/search/repositories?q=user:{username}"
    #     # TODO WE NEEDO TO GET ALL REPOS PUBLIC + INSTALLED. 
    #     # url = "https://api.github.com/installation/repositories"
    #     headers = {'Authorization': f'bearer {access_token}'}

    #     try:
    #         response = requests.get(url, headers=headers)
    #         response.raise_for_status()
    #         repos_data = response.json()
    #         repos = []
    #         for repo in repos_data:
    #             repos.append({'name': repo.get('name'), 'owner': repo.get('owner').get('login')})
    #     except HTTPError as e:
    #         logging.error(f"HTTP error occurred: {e}")
    #         raise e
    #     except Exception as e:
    #         logging.error(f"An error occurred: {e}")
    #         raise e
    #     else:
    #         return repos
    
    def get_installation_repos(self, jwt: str, access_token:str) -> list:
        installations_url = "https://api.github.com/user/installations"
        headers = {
            'Authorization': f'Bearer {access_token}', 
            'Accept': 'application/vnd.github+json'
        }

        try:
            response = requests.get(installations_url, headers=headers)
            response.raise_for_status()
            installations = response.json().get('installations', [])

            all_repos = []
            for installation in installations:
                installation_id = installation['id']
                installation_token = self.get_installation_access_token(jwt, installation_id)
                    
                if installation_token:
                    repos_url = f"https://api.github.com/installation/repositories"
                    repos_headers = {
                        'Authorization': f'token {installation_token}',
                        'Accept': 'application/vnd.github+json'
                    }
                    repos_response = requests.get(repos_url, headers=repos_headers)
                    repos_response.raise_for_status()
                    repos_data = repos_response.json().get('repositories', [])
                    
                    for repo in repos_data:
                        all_repos.append({
                            'name': repo.get('name'),
                            'owner': repo.get('owner').get('login')
                        })

        except HTTPError as e:
            # Handle rate limits specifically
            if e.response.status_code == 403 and 'X-RateLimit-Remaining' in e.response.headers and int(e.response.headers['X-RateLimit-Remaining']) == 0:
                logging.error("Rate limit exceeded!")
            else:
                logging.error(f"HTTP error occurred: {e}")
            raise e
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            raise e
        else:
            return all_repos

        
    def get_installation_access_token(self, jwt: str, installation_id: int) -> str:
        access_token_url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        headers = {
            'Authorization': f'Bearer {jwt}', 
            'Accept': 'application/vnd.github+json'
        }

        
        try:
            response = requests.post(access_token_url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get('token')
        except Exception as e:
            logging.error(f"Failed to get installation access token: {e}")
            return None
        
    def create_issue(self, access_token: str, repository: str, owner: str, title: str, body: str):
        url = f"https://api.github.com/repos/{owner}/{repository}/issues"
        headers = {'Authorization': f'bearer {access_token}'}
        data = {
            'title': title,
            'body': body
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            issue_data = response.json()
            html_url = issue_data.get('html_url')

        except HTTPError as e:
            logging.error(f"HTTP error occurred: {e}")
            raise e
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            raise e
        else:
            return html_url

