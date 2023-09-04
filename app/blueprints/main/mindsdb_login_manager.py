import logging
import mindsdb_sdk
from requests.exceptions import HTTPError
from flask_jwt_extended import get_jwt_identity


class MindsDBLoginManager:
    def __init__(self):
        # TODO: save server objects in database/cache
        self.server_connection_objects = {}

    def login(self, login, password):
        try:
            # connect to mindsdb server and generate access token
            server = mindsdb_sdk.connect(login=login, password=password)

            # save server object
            self.save_server_connection_for_login(login=login, server=server)

            return True
        except HTTPError as e:
            logging.error(e)
            return False
        
    def save_server_connection_for_login(self, login, server):
        self.server_connection_objects[login] = server

    def get_server_connection_for_login(self):
        # get login from jwt
        login = get_jwt_identity()

        # get server object
        server = self.server_connection_objects.get(login)

        # if server object exists, get databases
        if server:
            return server

        # else return error
        else:
            return None