import logging
import mindsdb_sdk
from requests.exceptions import HTTPError


class MindsDBLoginManager:
    def __init__(self):
        # TODO: save server objects in database/cache
        self.server_connection_objects = {}

    def login(self, login, password):
        try:
            # connect to mindsdb server
            mindsdb_sdk.connect(login=login, password=password)
            return True
        except HTTPError as e:
            logging.error(e)
            return False
        